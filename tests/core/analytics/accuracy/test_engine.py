import pytest
import pandas as pd
import math
import uuid
from datetime import datetime

from core.foundation.enums import Environment, ExecutionMode
from core.foundation.execution_context import ExecutionContext
from core.config.models import (
    EnterpriseConfig, PlatformConfig, AnalyticsConfig, 
    DecisionPolicyConfig, ContentConfig, RendererConfig, EnvironmentConfig
)
from core.contracts.dataset import (
    PreparedAnalyticsDataset, PreparedSegmentMetadata, 
    PreparationSummary, WindowMetadata, DatasetReference
)
from core.analytics.accuracy.engine import ForecastAccuracyEngine
from core.contracts.analytics import ForecastAccuracyResult
from core.validation.exceptions import AnalyticsException

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

@pytest.fixture
def get_config():
    def _config(policy="RETURN_INFINITY", tol=0.10):
        return EnterpriseConfig(
            platform=PlatformConfig("1.0", "INFO", 300, 3, "1.0"),
            analytics=AnalyticsConfig(
                enable_ml_metrics=True, 
                winsorization_percentile=0.95, 
                coverage_threshold_percent=0.8, 
                minimum_sample_size=1, 
                segmentation_keys=("segment_id",), 
                acceptable_tolerance_percentage=tol, 
                zero_actuals_policy=policy,
                standard_alpha=0.05,
                high_confidence_alpha=0.01,
                practical_improvement_threshold_percent=0.05,
                minimum_statistical_sample_size=5,
                minimum_effect_size=0.1
            ),
            decision=DecisionPolicyConfig(0.05, 2, 0.85, "HIGH", "RECENT_ACCURACY"),
            content=ContentConfig(True, True, 5),
            renderer=RendererConfig("PDF", True, "ENTERPRISE_DARK"),
            environment=EnvironmentConfig(Environment.DEV, True, True)
        )
    return _config

def create_mock_prepared_dataset(tmp_path, context, data_dict):
    df = pd.DataFrame(data_dict)
    csv_path = str(tmp_path / "mock_prepared.csv")
    df.to_csv(csv_path, index=False)
    
    ref = DatasetReference("LOCAL_CSV", csv_path)
    
    seg_meta = []
    for s in df['segment_id'].unique():
        seg_meta.append(PreparedSegmentMetadata(segment_id=str(s), is_eligible=True, observation_count=len(df[df['segment_id']==s])))
        
    return PreparedAnalyticsDataset(
        execution_context=context,
        prepared_reference=ref,
        prepared_data_hash="hash",
        segment_metadata=tuple(seg_meta),
        preparation_summary=PreparationSummary(len(df), len(df), len(df), len(df)),
        window_metadata=WindowMetadata(datetime.utcnow(), datetime.utcnow(), 1),
        total_eligible_segments=len(seg_meta),
        total_disqualified_segments=0,
        preparation_timestamp=datetime.utcnow()
    )

def test_perfect_forecast(tmp_path, dummy_context, get_config):
    data = {
        "segment_id": ["A", "A", "A"],
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "actual": [10.0, 20.0, 30.0],
        "forecast": [10.0, 20.0, 30.0]
    }
    dataset = create_mock_prepared_dataset(tmp_path, dummy_context, data)
    
    engine = ForecastAccuracyEngine(get_config())
    result = engine.execute(dataset)
    
    assert len(result.segment_metrics) == 1
    seg_A = result.segment_metrics[0]
    
    assert seg_A.wape == 0.0
    assert seg_A.bias == 0.0
    assert seg_A.mae == 0.0
    assert seg_A.rmse == 0.0
    assert seg_A.hit_rate == 1.0
    
    assert result.global_metrics.global_wape == 0.0
    assert result.global_metrics.global_bias == 0.0
    assert result.global_metrics.volume_weighted_hit_rate == 1.0

def test_zero_actuals_infinity(tmp_path, dummy_context, get_config):
    data = {
        "segment_id": ["A", "A"],
        "date": ["2026-01-01", "2026-01-02"],
        "actual": [0.0, 0.0],
        "forecast": [10.0, 20.0]
    }
    dataset = create_mock_prepared_dataset(tmp_path, dummy_context, data)
    
    engine = ForecastAccuracyEngine(get_config(policy="RETURN_INFINITY"))
    result = engine.execute(dataset)
    
    seg_A = result.segment_metrics[0]
    assert math.isinf(seg_A.wape)
    assert seg_A.wape > 0
    assert math.isinf(seg_A.bias)
    assert seg_A.hit_rate == 0.0
    assert seg_A.mae == 15.0
    
    # Global metrics
    assert math.isinf(result.global_metrics.global_wape)
    assert math.isinf(result.global_metrics.global_bias)

def test_zero_actuals_perfect_forecast(tmp_path, dummy_context, get_config):
    data = {
        "segment_id": ["A"],
        "date": ["2026-01-01"],
        "actual": [0.0],
        "forecast": [0.0]
    }
    dataset = create_mock_prepared_dataset(tmp_path, dummy_context, data)
    
    engine = ForecastAccuracyEngine(get_config(policy="RETURN_INFINITY"))
    result = engine.execute(dataset)
    
    seg_A = result.segment_metrics[0]
    assert seg_A.wape == 0.0 # 0/0 error is treated as perfect 0.0
    assert seg_A.bias == 0.0
    assert seg_A.hit_rate == 1.0 # 0 <= 0*0 is True

def test_negative_actuals(tmp_path, dummy_context, get_config):
    data = {
        "segment_id": ["A"],
        "date": ["2026-01-01"],
        "actual": [-10.0],
        "forecast": [10.0]
    }
    dataset = create_mock_prepared_dataset(tmp_path, dummy_context, data)
    
    engine = ForecastAccuracyEngine(get_config())
    with pytest.raises(AnalyticsException, match="Negative actuals detected"):
        engine.execute(dataset)

def test_multiple_segments_aggregation(tmp_path, dummy_context, get_config):
    data = {
        "segment_id": ["A", "A", "B", "B"],
        "date": ["2026-01-01", "2026-01-02", "2026-01-01", "2026-01-02"],
        "actual": [100.0, 100.0, 10.0, 10.0],   # Sum_A = 200, Sum_B = 20
        "forecast": [110.0, 110.0, 5.0, 5.0]    # Err_A = +20, Err_B = -10. AbsErr_A = 20, AbsErr_B = 10
    }
    dataset = create_mock_prepared_dataset(tmp_path, dummy_context, data)
    
    engine = ForecastAccuracyEngine(get_config())
    result = engine.execute(dataset)
    
    # Segment A:
    # WAPE = 20/200 = 0.10
    # Bias = 20/200 = 0.10
    # MAE = 10
    # RMSE = 10
    # Hit10: errors are exactly 10 <= 10 (10% of 100). Wait, 110-100 = 10. Tolerance is 0.1*100=10. So hits = 2. rate = 1.0
    
    # Segment B:
    # WAPE = 10/20 = 0.50
    # Bias = -10/20 = -0.50
    # MAE = 5
    # RMSE = 5
    # Hit10: error 5. 5 <= 0.1*10 = 1. False. rate = 0.0
    
    seg_A = next(s for s in result.segment_metrics if s.segment_id == "A")
    assert math.isclose(seg_A.wape, 0.10)
    assert math.isclose(seg_A.bias, 0.10)
    assert math.isclose(seg_A.hit_rate, 1.0)
    
    seg_B = next(s for s in result.segment_metrics if s.segment_id == "B")
    assert math.isclose(seg_B.wape, 0.50)
    assert math.isclose(seg_B.bias, -0.50)
    assert math.isclose(seg_B.hit_rate, 0.0)
    
    # Global
    # AbsError = 20 + 10 = 30
    # Error = 20 + (-10) = 10
    # ActualSum = 200 + 20 = 220
    # Global WAPE = 30 / 220 = 0.136363...
    # Global Bias = 10 / 220 = 0.045454...
    assert math.isclose(result.global_metrics.global_wape, 30.0/220.0)
    assert math.isclose(result.global_metrics.global_bias, 10.0/220.0)
    
    # Volume Weighted MAE
    # A_MAE = 10, A_Vol = 200 -> 2000
    # B_MAE = 5, B_Vol = 20 -> 100
    # Weighted MAE = 2100 / 220 = 9.5454...
    assert math.isclose(result.global_metrics.volume_weighted_mae, 2100.0/220.0)
