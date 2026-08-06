import math
import pytest
import pandas as pd
from datetime import datetime
from core.foundation.execution_context import ExecutionContext
from core.foundation.enums import Environment
from core.config.models import EnterpriseConfig, AnalyticsConfig, DecisionPolicyConfig, ContentConfig, RendererConfig, PlatformConfig, EnvironmentConfig
from core.contracts.dataset import PreparedAnalyticsDataset, DatasetReference, WindowMetadata, PreparedSegmentMetadata, PreparationSummary
from core.analytics.statistical.engine import StatisticalAnalyticsEngine
from core.validation.exceptions import AnalyticsException

@pytest.fixture
def dummy_config():
    return EnterpriseConfig(
        platform=PlatformConfig("1.0", "INFO", 300, 3, "1.0"),
        analytics=AnalyticsConfig(
            enable_ml_metrics=True, 
            winsorization_percentile=0.95, 
            coverage_threshold_percent=0.8, 
            minimum_sample_size=1, 
            segmentation_keys=("segment_id",), 
            acceptable_tolerance_percentage=0.10, 
            zero_actuals_policy="RETURN_INFINITY",
            standard_alpha=0.05,
            high_confidence_alpha=0.01,
            practical_improvement_threshold_percent=0.05,
            minimum_statistical_sample_size=5,
            minimum_effect_size=0.1
        ),
        decision=DecisionPolicyConfig(0.05, 2, 0.85, "HIGH", "RECENT_ACCURACY"),
        content=ContentConfig(True, True, 5),
        renderer=RendererConfig("PDF", True, "ENTERPRISE_DARK"),
        environment=EnvironmentConfig(Environment.TEST, True, True)
    )

import uuid
from core.foundation.enums import Environment, ExecutionMode

def create_mock_prepared_dataset(df: pd.DataFrame, tmp_path, prefix: str) -> PreparedAnalyticsDataset:
    file_path = tmp_path / f"{prefix}_data.csv"
    df.to_csv(file_path, index=False)
    
    ctx = ExecutionContext(
        run_id=uuid.uuid4(),
        correlation_id="test_req",
        execution_timestamp=datetime.utcnow(),
        platform_version="1.0",
        environment=Environment.TEST,
        execution_mode=ExecutionMode.BATCH,
        user_id="test_user",
        request_source="pytest",
        config_versions=(("analytics", "1.0"),),
        traceability_id=uuid.uuid4()
    )
    
    return PreparedAnalyticsDataset(
        execution_context=ctx,
        prepared_reference=DatasetReference("LOCAL_CSV", str(file_path)),
        prepared_data_hash="hash123",
        segment_metadata=(PreparedSegmentMetadata("SEG1", True, len(df)),),
        preparation_summary=PreparationSummary(len(df), len(df), len(df), len(df)),
        window_metadata=WindowMetadata(datetime.utcnow(), datetime.utcnow(), 1),
        total_eligible_segments=1,
        total_disqualified_segments=0,
        preparation_timestamp=datetime.utcnow()
    )

def test_identical_models(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates = pd.date_range("2026-01-01", periods=5)
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": [100, 100, 100, 100, 100], "forecast": [90, 80, 85, 88, 90]})
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": [100, 100, 100, 100, 100], "forecast": [90, 80, 85, 88, 90]})
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec")
    
    result = engine.execute(prim_dataset, sec_dataset)
    
    seg_stats = result.segment_statistics[0]
    assert math.isnan(seg_stats.p_value)
    assert not seg_stats.is_practically_significant
    assert seg_stats.confidence_level == "SUPPRESSED"
    assert seg_stats.suppression_reason == "Zero Variance in Errors"

def test_clear_winner(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates = pd.date_range("2026-01-01", periods=6)
    # Scenario 2 from workbook
    # AbsErr A (Baseline/Sec) = [20, 25, 22, 28, 30, 25] (Sum = 150)
    # AbsErr B (Challenger/Prim) = [10, 15, 12, 18, 20, 15] (Sum = 90)
    # Note: actual - forecast = error. Let actual = 100.
    # Sec forecast = 100 - [20, 25, 22, 28, 30, 25] = [80, 75, 78, 72, 70, 75]
    # Prim forecast = 100 - [10, 15, 12, 18, 20, 15] = [90, 85, 88, 82, 80, 85]
    
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 100, "forecast": [80, 75, 78, 72, 70, 75]})
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 100, "forecast": [90, 85, 88, 82, 80, 85]})
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim2")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec2")
    
    result = engine.execute(prim_dataset, sec_dataset)
    
    seg_stats = result.segment_statistics[0]
    
    assert math.isclose(seg_stats.p_value, 0.015625, abs_tol=1e-4)
    assert seg_stats.is_practically_significant
    assert seg_stats.confidence_level == "MEDIUM"

def test_statistically_insignificant(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates = pd.date_range("2026-01-01", periods=6)
    # Scenario 3: +10, -10, +10, -10, +10, -10
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 100, "forecast": [90, 80, 70, 60, 50, 40]}) # Errors: 10, 20, 30, 40, 50, 60
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 100, "forecast": [80, 90, 60, 70, 40, 50]}) # Errors: 20, 10, 40, 30, 60, 50
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim3")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec3")
    
    result = engine.execute(prim_dataset, sec_dataset)
    
    seg_stats = result.segment_statistics[0]
    # For alternating perfectly matched ranks in one-sided test, p=0.5
    # Wait, the Wilcoxon T is perfectly half. p-value for two-sided is 1.0, one-sided is 0.5.
    assert not seg_stats.is_practically_significant
    assert seg_stats.confidence_level == "LOW"

def test_tiny_but_significant_massive_n(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates = pd.date_range("2026-01-01", periods=1000)
    # Scenario 4: Massive N
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 200, "forecast": 99.9}) # Err 100.1
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 200, "forecast": 100.0}) # Err 100.0
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim4")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec4")
    
    result = engine.execute(prim_dataset, sec_dataset)
    
    seg_stats = result.segment_statistics[0]
    assert seg_stats.p_value < 0.01
    assert not seg_stats.is_practically_significant
    assert seg_stats.confidence_level == "MEDIUM"

def test_practical_but_insignificant_small_n(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates = pd.date_range("2026-01-01", periods=6)
    # Scenario 5
    # AbsErr Sec = [100, 100, 100, 100, 100, 100]
    # AbsErr Prim = [10, 100, 100, 100, 100, 100]
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 200, "forecast": 100})
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 200, "forecast": [190, 100, 100, 100, 100, 100]})
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim5")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec5")
    
    result = engine.execute(prim_dataset, sec_dataset)
    
    seg_stats = result.segment_statistics[0]
    assert seg_stats.p_value > 0.05
    assert seg_stats.is_practically_significant
    assert seg_stats.confidence_level == "LOW"

def test_insufficient_sample_size(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates = pd.date_range("2026-01-01", periods=3)
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 200, "forecast": 100})
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates, "actual": 200, "forecast": 110})
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim6")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec6")
    
    result = engine.execute(prim_dataset, sec_dataset)
    
    seg_stats = result.segment_statistics[0]
    assert math.isnan(seg_stats.p_value)
    assert seg_stats.is_practically_significant
    assert seg_stats.confidence_level == "INSUFFICIENT"
    assert "Sample size" in seg_stats.suppression_reason

def test_missing_paired_observations(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates_prim = pd.date_range("2026-01-01", periods=6)
    dates_sec = pd.date_range("2026-01-01", periods=3)
    
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates_prim, "actual": 200, "forecast": 110})
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates_sec, "actual": 200, "forecast": 100})
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim7")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec7")
    
    result = engine.execute(prim_dataset, sec_dataset)
    
    seg_stats = result.segment_statistics[0]
    # N=3 after inner join
    assert seg_stats.paired_observation_count == 3
    assert seg_stats.confidence_level == "INSUFFICIENT"

def test_zero_paired_observations(dummy_config, tmp_path):
    engine = StatisticalAnalyticsEngine(dummy_config)
    
    dates_prim = pd.date_range("2026-01-01", periods=6)
    dates_sec = pd.date_range("2026-02-01", periods=6) # No overlap
    
    df_prim = pd.DataFrame({"segment_id": "SEG1", "date": dates_prim, "actual": 200, "forecast": 110})
    df_sec = pd.DataFrame({"segment_id": "SEG1", "date": dates_sec, "actual": 200, "forecast": 100})
    
    prim_dataset = create_mock_prepared_dataset(df_prim, tmp_path, "prim8")
    sec_dataset = create_mock_prepared_dataset(df_sec, tmp_path, "sec8")
    
    with pytest.raises(AnalyticsException) as excinfo:
        engine.execute(prim_dataset, sec_dataset)
        
    assert excinfo.value.error_code == "STAT-002"
