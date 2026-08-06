import pytest
import uuid
from datetime import datetime, timezone
import math

from core.foundation.execution_context import ExecutionContext
from core.foundation.enums import Environment, ExecutionMode
from core.config.models import EnterpriseConfig, PlatformConfig, AnalyticsConfig, DecisionPolicyConfig, ContentConfig, RendererConfig, EnvironmentConfig
from core.contracts.dataset import DatasetReference, WindowMetadata
from core.contracts.analytics import (
    ForecastAccuracyResult, 
    MetricMetadata, 
    SegmentAccuracyMetrics, 
    GlobalAccuracyMetrics,
    StatisticalAnalyticsResult,
    SegmentStatisticalMetrics,
    GlobalStatisticalMetrics,
    AnalyticalEvidenceBundle
)
from core.analytics.consolidation.engine import AnalyticalEvidenceConsolidationEngine
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

def _create_mock_context(run_id=None):
    return ExecutionContext(
        run_id=run_id or uuid.uuid4(),
        correlation_id="test_req",
        execution_timestamp=datetime.now(timezone.utc),
        platform_version="1.0",
        environment=Environment.TEST,
        execution_mode=ExecutionMode.BATCH,
        user_id="test_user",
        request_source="pytest",
        config_versions=(("analytics", "1.0"),),
        traceability_id=uuid.uuid4()
    )

def _create_mock_accuracy_result(context, dataset_ref, window):
    return ForecastAccuracyResult(
        execution_context=context,
        prepared_dataset_reference=dataset_ref,
        evaluation_window=window,
        metric_metadata=MetricMetadata("1.0", datetime.now(timezone.utc), "RETURN_INFINITY", 0.1),
        segment_metrics=(SegmentAccuracyMetrics("SEG1", 100, 0.05, 0.0, 10.0, 15.0, 0.9),),
        global_metrics=GlobalAccuracyMetrics(100, 0.05, 0.0, 10.0, 15.0, 0.9)
    )

def _create_mock_statistical_result(context, primary_ref, secondary_ref):
    return StatisticalAnalyticsResult(
        execution_context=context,
        primary_dataset_reference=primary_ref,
        secondary_dataset_reference=secondary_ref,
        segment_statistics=(SegmentStatisticalMetrics("SEG1", 100, 0.01, 0.5, True, "HIGH", None),),
        global_statistics=GlobalStatisticalMetrics(100, 0.01, 0.5, True, "HIGH"),
        warnings=()
    )

def test_successful_consolidation_all_evidence(dummy_config):
    engine = AnalyticalEvidenceConsolidationEngine(dummy_config)
    run_id = uuid.uuid4()
    ctx = _create_mock_context(run_id)
    window = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 1)
    
    prim_ref = DatasetReference("LOCAL_CSV", "/tmp/prim.csv")
    sec_ref = DatasetReference("LOCAL_CSV", "/tmp/sec.csv")
    
    prim_acc = _create_mock_accuracy_result(ctx, prim_ref, window)
    sec_acc = _create_mock_accuracy_result(ctx, sec_ref, window)
    stat_res = _create_mock_statistical_result(ctx, prim_ref, sec_ref)
    
    bundle = engine.execute(
        primary_id="MODEL_A",
        primary_accuracy=prim_acc,
        secondary_id="MODEL_B",
        secondary_accuracy=sec_acc,
        statistical_result=stat_res
    )
    
    assert isinstance(bundle, AnalyticalEvidenceBundle)
    assert bundle.primary_evidence.model_identifier == "MODEL_A"
    assert bundle.secondary_evidence.model_identifier == "MODEL_B"
    assert bundle.primary_evidence.statistical_metrics == stat_res
    assert bundle.execution_context.run_id == run_id

def test_successful_consolidation_primary_only(dummy_config):
    engine = AnalyticalEvidenceConsolidationEngine(dummy_config)
    ctx = _create_mock_context()
    window = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 1)
    prim_ref = DatasetReference("LOCAL_CSV", "/tmp/prim.csv")
    
    prim_acc = _create_mock_accuracy_result(ctx, prim_ref, window)
    
    bundle = engine.execute(
        primary_id="MODEL_A",
        primary_accuracy=prim_acc
    )
    
    assert bundle.secondary_evidence is None
    assert bundle.primary_evidence.statistical_metrics is None

def test_failure_context_mismatch(dummy_config):
    engine = AnalyticalEvidenceConsolidationEngine(dummy_config)
    ctx1 = _create_mock_context()
    ctx2 = _create_mock_context() # different run_id
    
    window = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 1)
    prim_ref = DatasetReference("LOCAL_CSV", "/tmp/prim.csv")
    sec_ref = DatasetReference("LOCAL_CSV", "/tmp/sec.csv")
    
    prim_acc = _create_mock_accuracy_result(ctx1, prim_ref, window)
    sec_acc = _create_mock_accuracy_result(ctx2, sec_ref, window)
    
    with pytest.raises(AnalyticsException) as exc:
        engine.execute(
            primary_id="MODEL_A",
            primary_accuracy=prim_acc,
            secondary_id="MODEL_B",
            secondary_accuracy=sec_acc
        )
    assert exc.value.error_code == "EVAL-001"

def test_failure_temporal_mismatch(dummy_config):
    engine = AnalyticalEvidenceConsolidationEngine(dummy_config)
    ctx = _create_mock_context()
    
    window1 = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 1)
    window2 = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 2)
    
    prim_ref = DatasetReference("LOCAL_CSV", "/tmp/prim.csv")
    sec_ref = DatasetReference("LOCAL_CSV", "/tmp/sec.csv")
    
    prim_acc = _create_mock_accuracy_result(ctx, prim_ref, window1)
    sec_acc = _create_mock_accuracy_result(ctx, sec_ref, window2)
    
    with pytest.raises(AnalyticsException) as exc:
        engine.execute("MODEL_A", prim_acc, "MODEL_B", sec_acc)
    assert exc.value.error_code == "EVAL-002"

def test_failure_missing_evidence(dummy_config):
    engine = AnalyticalEvidenceConsolidationEngine(dummy_config)
    ctx = _create_mock_context()
    window = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 1)
    prim_ref = DatasetReference("LOCAL_CSV", "/tmp/prim.csv")
    prim_acc = _create_mock_accuracy_result(ctx, prim_ref, window)
    
    with pytest.raises(AnalyticsException) as exc:
        engine.execute("MODEL_A", prim_acc, secondary_id="MODEL_B") # Missing secondary_accuracy
    assert exc.value.error_code == "EVAL-007"
    
def test_failure_dataset_mismatch(dummy_config):
    engine = AnalyticalEvidenceConsolidationEngine(dummy_config)
    ctx = _create_mock_context()
    window = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 1)
    
    prim_ref = DatasetReference("LOCAL_CSV", "/tmp/prim.csv")
    sec_ref = DatasetReference("LOCAL_CSV", "/tmp/sec.csv")
    wrong_ref = DatasetReference("LOCAL_CSV", "/tmp/wrong.csv")
    
    prim_acc = _create_mock_accuracy_result(ctx, prim_ref, window)
    sec_acc = _create_mock_accuracy_result(ctx, sec_ref, window)
    stat_res = _create_mock_statistical_result(ctx, wrong_ref, sec_ref)
    
    with pytest.raises(AnalyticsException) as exc:
        engine.execute("MODEL_A", prim_acc, "MODEL_B", sec_acc, stat_res)
    assert exc.value.error_code == "EVAL-004"
