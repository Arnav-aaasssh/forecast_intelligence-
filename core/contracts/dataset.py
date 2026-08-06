from dataclasses import dataclass
from typing import Tuple, Optional
from datetime import datetime
from core.foundation.execution_context import ExecutionContext
from .exceptions import ContractValidationException

@dataclass(frozen=True)
class DatasetReference:
    """Storage abstraction for physical datasets."""
    backend_type: str # e.g. 'S3', 'LOCAL_PARQUET', 'SQL'
    uri: str
    credential_reference: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.backend_type, str) or not self.backend_type.strip():
            raise ContractValidationException("backend_type must be a non-empty string.")
        if not isinstance(self.uri, str) or not self.uri.strip():
            raise ContractValidationException("uri must be a non-empty string.")

@dataclass(frozen=True)
class ValidatedDataset:
    """Represents validated business data ready for Preparation."""
    execution_context: ExecutionContext
    reference: DatasetReference
    schema_version: str
    row_count: int
    column_count: int
    missing_values: int
    time_series_count: int
    data_hash: str

    def __post_init__(self):
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.reference, DatasetReference):
            raise ContractValidationException("reference must be a valid DatasetReference.")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ContractValidationException("schema_version must be a non-empty string.")
        if not isinstance(self.row_count, int) or self.row_count < 0:
            raise ContractValidationException("row_count must be a non-negative integer.")
        if not isinstance(self.column_count, int) or self.column_count < 0:
            raise ContractValidationException("column_count must be a non-negative integer.")
        if not isinstance(self.missing_values, int) or self.missing_values < 0:
            raise ContractValidationException("missing_values must be a non-negative integer.")
        if not isinstance(self.time_series_count, int) or self.time_series_count < 0:
            raise ContractValidationException("time_series_count must be a non-negative integer.")
        if not isinstance(self.data_hash, str) or not self.data_hash.strip():
            raise ContractValidationException("data_hash must be a non-empty string.")

@dataclass(frozen=True)
class PreparedSegmentMetadata:
    segment_id: str
    is_eligible: bool
    observation_count: int
    disqualification_reason: Optional[str] = None

@dataclass(frozen=True)
class PreparationSummary:
    initial_row_count: int
    filtered_row_count: int
    canonicalized_row_count: int
    final_row_count: int

@dataclass(frozen=True)
class WindowMetadata:
    evaluation_start: datetime
    evaluation_end: datetime
    periods_included: int

@dataclass(frozen=True)
class PreparedAnalyticsDataset:
    """Immutable DTO guaranteeing dataset is grouped, canonicalized, and segmented for Analytics execution."""
    execution_context: ExecutionContext
    prepared_reference: DatasetReference
    prepared_data_hash: str
    segment_metadata: Tuple[PreparedSegmentMetadata, ...]
    preparation_summary: PreparationSummary
    window_metadata: WindowMetadata
    total_eligible_segments: int
    total_disqualified_segments: int
    preparation_timestamp: datetime

    def __post_init__(self):
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.prepared_reference, DatasetReference):
            raise ContractValidationException("prepared_reference must be a DatasetReference.")
        if not isinstance(self.prepared_data_hash, str) or not self.prepared_data_hash.strip():
            raise ContractValidationException("prepared_data_hash must be a non-empty string.")
        if not isinstance(self.segment_metadata, tuple):
            raise ContractValidationException("segment_metadata must be a tuple.")
        if not isinstance(self.preparation_summary, PreparationSummary):
            raise ContractValidationException("preparation_summary must be a PreparationSummary.")
        if not isinstance(self.window_metadata, WindowMetadata):
            raise ContractValidationException("window_metadata must be a WindowMetadata.")
        if not isinstance(self.total_eligible_segments, int) or self.total_eligible_segments < 0:
            raise ContractValidationException("total_eligible_segments must be a non-negative int.")
        if not isinstance(self.total_disqualified_segments, int) or self.total_disqualified_segments < 0:
            raise ContractValidationException("total_disqualified_segments must be a non-negative int.")
        if not isinstance(self.preparation_timestamp, datetime):
            raise ContractValidationException("preparation_timestamp must be a datetime.")
