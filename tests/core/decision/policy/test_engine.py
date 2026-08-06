import pytest
import uuid
import math
from datetime import datetime, timezone

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
    AnalyticalEvidenceBundle,
    ModelEvidence
)
from core.contracts.decision import PolicyEvaluation, PolicyEvaluationMatrix
from core.decision.policy.engine import DecisionPolicyEngine
from core.decision.policy.registry import PolicyRegistry, create_default_registry
from core.decision.policy.policies import PolicyEvaluator, MLSuperiorityPolicy, ConfidencePolicy, CoveragePolicy
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

def _create_bundle(primary_wape=0.10, secondary_wape=0.15, hit_rate=0.90, p_value=0.01, confidence="HIGH", include_secondary=True, include_stats=True):
    ctx = _create_mock_context()
    window = WindowMetadata(datetime.now(timezone.utc), datetime.now(timezone.utc), 1)
    ref = DatasetReference("LOCAL_CSV", "/tmp/data.csv")
    
    prim_acc = ForecastAccuracyResult(
        execution_context=ctx,
        prepared_dataset_reference=ref,
        evaluation_window=window,
        metric_metadata=MetricMetadata("1.0", datetime.now(timezone.utc), "RETURN_INFINITY", 0.1),
        segment_metrics=(SegmentAccuracyMetrics("SEG1", 100, primary_wape, 0.0, 10.0, 15.0, hit_rate),),
        global_metrics=GlobalAccuracyMetrics(100, primary_wape, 0.0, 10.0, 15.0, hit_rate)
    )
    
    sec_acc = None
    if include_secondary:
        sec_acc = ForecastAccuracyResult(
            execution_context=ctx,
            prepared_dataset_reference=ref,
            evaluation_window=window,
            metric_metadata=MetricMetadata("1.0", datetime.now(timezone.utc), "RETURN_INFINITY", 0.1),
            segment_metrics=(SegmentAccuracyMetrics("SEG1", 100, secondary_wape, 0.0, 10.0, 15.0, hit_rate),),
            global_metrics=GlobalAccuracyMetrics(100, secondary_wape, 0.0, 10.0, 15.0, hit_rate)
        )
        
    stat_res = None
    if include_stats:
        stat_res = StatisticalAnalyticsResult(
            execution_context=ctx,
            primary_dataset_reference=ref,
            secondary_dataset_reference=ref,
            segment_statistics=(SegmentStatisticalMetrics("SEG1", 100, p_value, 0.5, True, confidence, None),),
            global_statistics=GlobalStatisticalMetrics(100, p_value, 0.5, True, confidence),
            warnings=()
        )
        
    return AnalyticalEvidenceBundle(
        primary_evidence=ModelEvidence("MODEL_A", True, prim_acc, stat_res),
        secondary_evidence=ModelEvidence("MODEL_B", False, sec_acc, None) if include_secondary else None,
        execution_context=ctx,
        traceability_id=uuid.uuid4(),
        consolidation_timestamp=datetime.now(timezone.utc)
    )

def test_ml_superiority_policy_pass(dummy_config):
    policy = MLSuperiorityPolicy()
    bundle = _create_bundle(primary_wape=0.10, secondary_wape=0.16)
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "PASS"
    assert res.reason_code == "PASSED"

def test_ml_superiority_policy_fail(dummy_config):
    policy = MLSuperiorityPolicy()
    bundle = _create_bundle(primary_wape=0.10, secondary_wape=0.12)
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "FAIL"
    assert res.reason_code == "FAILED_MARGIN"
    
def test_ml_superiority_policy_na_greenfield(dummy_config):
    policy = MLSuperiorityPolicy()
    bundle = _create_bundle(include_secondary=False)
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "NOT_APPLICABLE"
    assert res.reason_code == "NOT_APPLICABLE_GREENFIELD"
    
def test_ml_superiority_policy_na_nonfinite(dummy_config):
    policy = MLSuperiorityPolicy()
    bundle = _create_bundle(primary_wape=float('nan'), secondary_wape=0.12)
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "NOT_APPLICABLE"
    assert res.reason_code == "NOT_APPLICABLE_NONFINITE"

def test_confidence_policy_pass(dummy_config):
    policy = ConfidencePolicy()
    bundle = _create_bundle(confidence="HIGH")
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "PASS"
    assert res.reason_code == "PASSED"

def test_confidence_policy_fail(dummy_config):
    policy = ConfidencePolicy()
    bundle = _create_bundle(confidence="MEDIUM")
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "FAIL"
    assert res.reason_code == "FAILED_CONFIDENCE"
    
def test_confidence_policy_suppressed(dummy_config):
    policy = ConfidencePolicy()
    bundle = _create_bundle(confidence="SUPPRESSED")
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "SUPPRESSED"
    assert res.reason_code == "SUPPRESSED_STATS"

def test_coverage_policy_pass(dummy_config):
    policy = CoveragePolicy()
    bundle = _create_bundle(hit_rate=0.90)
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "PASS"
    assert res.reason_code == "PASSED"

def test_coverage_policy_fail(dummy_config):
    policy = CoveragePolicy()
    bundle = _create_bundle(hit_rate=0.80)
    res = policy.evaluate(bundle, dummy_config.decision)
    assert res.status == "FAIL"
    assert res.reason_code == "FAILED_COVERAGE"

def test_engine_success(dummy_config):
    engine = DecisionPolicyEngine(dummy_config)
    bundle = _create_bundle(primary_wape=0.10, secondary_wape=0.16, hit_rate=0.90, confidence="HIGH")
    matrix = engine.evaluate(bundle)
    
    assert isinstance(matrix, PolicyEvaluationMatrix)
    assert len(matrix.evaluations) == 3
    for ev in matrix.evaluations:
        assert ev.status == "PASS"

def test_engine_invalid_input(dummy_config):
    engine = DecisionPolicyEngine(dummy_config)
    with pytest.raises(AnalyticsException) as exc:
        engine.evaluate(None)
    assert exc.value.error_code == "DEC-001"
    
def test_engine_policy_error(dummy_config):
    class FaultyPolicy(PolicyEvaluator):
        @property
        def policy_name(self) -> str:
            return "FAULTY"
        def evaluate(self, bundle, config):
            raise ValueError("Something broke")
            
    registry = PolicyRegistry()
    registry.register(FaultyPolicy())
    
    engine = DecisionPolicyEngine(dummy_config, registry)
    bundle = _create_bundle()
    
    with pytest.raises(AnalyticsException) as exc:
        engine.evaluate(bundle)
    assert exc.value.error_code == "DEC-003"
    
def test_registry_duplicate_register():
    registry = PolicyRegistry()
    policy = CoveragePolicy()
    registry.register(policy)
    with pytest.raises(ValueError):
        registry.register(policy)
