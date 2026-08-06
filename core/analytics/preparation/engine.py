import pandas as pd
from datetime import datetime
from typing import Tuple, List, Optional
import uuid

from core.contracts.dataset import (
    ValidatedDataset, PreparedAnalyticsDataset, PreparedSegmentMetadata,
    PreparationSummary, WindowMetadata, DatasetReference
)
from core.validation.exceptions import DatasetValidationException
from core.config.models import EnterpriseConfig

class DatasetPreparationEngine:
    """
    Transforms a ValidatedDataset into a PreparedAnalyticsDataset.
    It cleanses, segments, and qualifies Time-Series data for deterministic downstream Analytics execution.
    NO mathematical evaluation (WAPE/Bias/Ranking) takes place here.
    """
    def __init__(self, config: EnterpriseConfig):
        self.config = config
    
    def execute(self, validated_dataset: ValidatedDataset) -> PreparedAnalyticsDataset:
        start_time = datetime.utcnow()
        
        # 1. Dataset Loading
        df = self._load_data(validated_dataset.reference)
        initial_row_count = len(df)
        
        # 2. Canonicalization
        df = self._canonicalize(df)
        canonicalized_row_count = len(df)
        
        # 3. Temporal Preparation
        df, window_meta = self._prepare_temporal_window(df)
        filtered_row_count = len(df)
        
        # 4. Grouping & Segmentation (Coverage Qualification)
        df, segment_metadata_list = self._segment_and_qualify(df)
        
        # 5. Serialization
        prepared_ref = self._serialize_prepared_data(df, validated_dataset.reference)
        
        # 6. Metadata generation
        total_eligible = sum(1 for m in segment_metadata_list if m.is_eligible)
        total_disqualified = len(segment_metadata_list) - total_eligible
        
        prep_summary = PreparationSummary(
            initial_row_count=initial_row_count,
            canonicalized_row_count=canonicalized_row_count,
            filtered_row_count=filtered_row_count,
            final_row_count=len(df)
        )
        
        # Construct output contract
        return PreparedAnalyticsDataset(
            execution_context=validated_dataset.execution_context,
            prepared_reference=prepared_ref,
            prepared_data_hash=str(uuid.uuid4()),  # In a real environment, cryptographic hash of the prepared bytes
            segment_metadata=tuple(segment_metadata_list),
            preparation_summary=prep_summary,
            window_metadata=window_meta,
            total_eligible_segments=total_eligible,
            total_disqualified_segments=total_disqualified,
            preparation_timestamp=datetime.utcnow()
        )
        
    def _load_data(self, ref: DatasetReference) -> pd.DataFrame:
        if ref.backend_type == "LOCAL_PARQUET":
            try:
                return pd.read_parquet(ref.uri)
            except Exception as e:
                raise DatasetValidationException("DATA-001", "Storage", f"Failed to load dataset: {str(e)}", "Check URI")
        elif ref.backend_type == "LOCAL_CSV":
            try:
                return pd.read_csv(ref.uri)
            except Exception as e:
                raise DatasetValidationException("DATA-001", "Storage", f"Failed to load dataset: {str(e)}", "Check URI")
        else:
            raise DatasetValidationException("DATA-002", "Storage", f"Unsupported backend: {ref.backend_type}", "Use LOCAL_PARQUET or LOCAL_CSV")
            
    def _canonicalize(self, df: pd.DataFrame) -> pd.DataFrame:
        keys = self.config.analytics.segmentation_keys
        for k in keys:
            if k not in df.columns:
                raise DatasetValidationException("DATA-003", "Schema", f"Missing segmentation key: {k}", "Ensure dataset matches configuration schema")
            
            # Canonicalize segmentation keys: trim whitespace and uppercase
            df[k] = df[k].astype(str).str.strip().str.upper()
                
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        else:
            raise DatasetValidationException("DATA-003", "Schema", "Missing required 'date' column.", "Schema must include temporal column 'date'.")
            
        return df
        
    def _prepare_temporal_window(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, WindowMetadata]:
        # Sort chronologically
        df = df.sort_values(by='date').reset_index(drop=True)
        
        if df.empty:
            now = datetime.utcnow()
            return df, WindowMetadata(evaluation_start=now, evaluation_end=now, periods_included=0)
            
        start_date = df['date'].min()
        end_date = df['date'].max()
        periods = int(df['date'].nunique())
        
        wm = WindowMetadata(
            evaluation_start=start_date.to_pydatetime() if hasattr(start_date, 'to_pydatetime') else start_date,
            evaluation_end=end_date.to_pydatetime() if hasattr(end_date, 'to_pydatetime') else end_date,
            periods_included=periods
        )
        return df, wm
        
    def _segment_and_qualify(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[PreparedSegmentMetadata]]:
        keys = list(self.config.analytics.segmentation_keys)
        
        if df.empty:
            return df, []
        
        # Partition Data (Dynamic Segmentation)
        if len(keys) > 1:
            df['segment_id'] = df[keys].astype(str).apply(lambda row: '_'.join(row), axis=1)
        else:
            df['segment_id'] = df[keys[0]].astype(str)
            
        min_sample = self.config.analytics.minimum_sample_size
        segment_metadata = []
        
        for seg_id, group in df.groupby('segment_id'):
            obs_count = len(group)
            
            # Enforce temporal uniqueness per segment
            if group['date'].duplicated().any():
                raise DatasetValidationException("DATA-004", "Temporal", f"Duplicate dates detected in segment: {seg_id}", "Resolve duplicate observation periods upstream.")
                
            is_eligible = obs_count >= min_sample
            reason = None if is_eligible else f"Observation count ({obs_count}) is below required AnalyticsConfig minimum ({min_sample})."
            
            segment_metadata.append(PreparedSegmentMetadata(
                segment_id=str(seg_id),
                is_eligible=is_eligible,
                observation_count=obs_count,
                disqualification_reason=reason
            ))
            
        return df, segment_metadata

    def _serialize_prepared_data(self, df: pd.DataFrame, original_ref: DatasetReference) -> DatasetReference:
        if original_ref.backend_type == "LOCAL_CSV":
            out_uri = original_ref.uri + ".prepared.csv"
            df.to_csv(out_uri, index=False)
            return DatasetReference(
                backend_type="LOCAL_CSV",
                uri=out_uri,
                credential_reference=original_ref.credential_reference
            )
        else:
            out_uri = original_ref.uri + ".prepared.parquet"
            return DatasetReference(
                backend_type="LOCAL_PARQUET",
                uri=out_uri,
                credential_reference=original_ref.credential_reference
            )
