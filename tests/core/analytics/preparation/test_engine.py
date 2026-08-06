import pytest
import os
import pandas as pd
from datetime import datetime
import uuid

from core.foundation.execution_context import ExecutionContext
from core.contracts.dataset import (
    ValidatedDataset, DatasetReference
)
from core.config.models import (
    EnterpriseConfig, PlatformConfig, AnalyticsConfig, 
    DecisionPolicyConfig, ContentConfig, RendererConfig, EnvironmentConfig
)
from core.foundation.enums import Environment, ExecutionMode
from core.validation.exceptions import DatasetValidationException
from core.analytics.preparation.engine import DatasetPreparationEngine

@pytest.fixture
def dummy_config():
    return EnterpriseConfig(
        platform=PlatformConfig("1.0", "INFO", 300, 3, "1.0"),
        analytics=AnalyticsConfig(True, 0.95, 0.8, 3, ("forecast_name", "region"), 0.10, "RETURN_INFINITY", 0.05, 0.01, 0.05, 5, 0.1),
        decision=DecisionPolicyConfig(0.05, 2, 0.85, "HIGH", "RECENT_ACCURACY"),
        content=ContentConfig(True, True, 5),
        renderer=RendererConfig("PDF", True, "ENTERPRISE_DARK"),
        environment=EnvironmentConfig(Environment.DEV, True, True)
    )

@pytest.fixture
def dummy_context():
    return ExecutionContext(
        run_id=uuid.uuid4(),
        correlation_id="corr-1",
        execution_timestamp=datetime.utcnow(),
        platform_version="1.0",
        environment=Environment.DEV,
        execution_mode=ExecutionMode.BATCH,
        user_id="test_user",
        request_source="pytest",
        config_versions=(("platform", "1.0"),),
        traceability_id=uuid.uuid4()
    )

def test_engine_successful_preparation(tmp_path, dummy_config, dummy_context):
    # Create mock dataset
    data = {
        "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-01", "2026-01-02"],
        "forecast_name": ["FCST_A", "fcst_a ", "FCST_A", "FCST_B", "FCST_B"],
        "region": ["NORTH_AM", "north_am ", "NORTH_AM", "EU", "EU"],
        "value": [10.0, 12.0, 14.0, 100.0, 110.0]
    }
    df = pd.DataFrame(data)
    csv_path = str(tmp_path / "mock_data.csv")
    df.to_csv(csv_path, index=False)
    
    ref = DatasetReference(backend_type="LOCAL_CSV", uri=csv_path)
    
    val_dataset = ValidatedDataset(
        execution_context=dummy_context,
        reference=ref,
        schema_version="1.0",
        row_count=5,
        column_count=4,
        missing_values=0,
        time_series_count=2,
        data_hash="fake-hash"
    )
    
    engine = DatasetPreparationEngine(dummy_config)
    prepared_dataset = engine.execute(val_dataset)
    
    assert prepared_dataset.total_eligible_segments == 1 # FCST_A_NA has 3 obs (>= 3 minimum_sample_size)
    assert prepared_dataset.total_disqualified_segments == 1 # FCST_B_EU has 2 obs (< 3 minimum_sample_size)
    
    assert prepared_dataset.preparation_summary.initial_row_count == 5
    assert prepared_dataset.preparation_summary.final_row_count == 5
    assert prepared_dataset.window_metadata.periods_included == 3
    
    # Assert file was written
    assert os.path.exists(prepared_dataset.prepared_reference.uri)
    out_df = pd.read_csv(prepared_dataset.prepared_reference.uri)
    assert "segment_id" in out_df.columns
    assert list(out_df[out_df['segment_id'] == 'FCST_A_NORTH_AM']['forecast_name'].unique()) == ['FCST_A']

def test_missing_schema_column(tmp_path, dummy_config, dummy_context):
    data = {
        "date": ["2026-01-01"],
        "forecast_name": ["FCST_A"]
        # missing region
    }
    df = pd.DataFrame(data)
    csv_path = str(tmp_path / "mock_data.csv")
    df.to_csv(csv_path, index=False)
    
    ref = DatasetReference(backend_type="LOCAL_CSV", uri=csv_path)
    val_dataset = ValidatedDataset(dummy_context, ref, "1.0", 1, 2, 0, 1, "hash")
    
    engine = DatasetPreparationEngine(dummy_config)
    
    with pytest.raises(DatasetValidationException, match="Missing segmentation key: region"):
        engine.execute(val_dataset)

def test_duplicate_dates(tmp_path, dummy_config, dummy_context):
    data = {
        "date": ["2026-01-01", "2026-01-01"], # duplicate date for same segment
        "forecast_name": ["FCST_A", "FCST_A"],
        "region": ["NORTH_AM", "NORTH_AM"],
        "value": [10.0, 12.0]
    }
    df = pd.DataFrame(data)
    csv_path = str(tmp_path / "mock_data.csv")
    df.to_csv(csv_path, index=False)
    
    ref = DatasetReference(backend_type="LOCAL_CSV", uri=csv_path)
    val_dataset = ValidatedDataset(dummy_context, ref, "1.0", 2, 4, 0, 1, "hash")
    
    engine = DatasetPreparationEngine(dummy_config)
    
    with pytest.raises(DatasetValidationException, match="Duplicate dates detected"):
        engine.execute(val_dataset)
