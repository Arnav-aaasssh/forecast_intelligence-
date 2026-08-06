import pytest
import uuid
from datetime import datetime, timezone

from core.foundation.execution_context import ExecutionContext
from core.foundation.enums import Environment, ExecutionMode
from core.config.models import EnterpriseConfig, PlatformConfig, AnalyticsConfig, DecisionPolicyConfig, ContentConfig, RendererConfig, EnvironmentConfig
from core.contracts.decision import PolicyEvaluation, PolicyEvaluationMatrix, DecisionContract
from core.decision.synthesis.synthesizer import DecisionSynthesizer, DecisionStateMachine, DecisionValidator
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

def _create_policy(name: str, status: str):
    return PolicyEvaluation(
        policy_name=name,
        status=status,
        reason_code="DUMMY",
        evaluated_metric_value=0.0,
        applied_threshold=0.0
    )

def _create_matrix(evaluations, ctx=None):
    return PolicyEvaluationMatrix(
        evaluations=tuple(evaluations),
        execution_context=ctx or _create_mock_context(),
        evidence_traceability_id=uuid.uuid4(),
        policy_version="1.0",
        evaluation_timestamp=datetime.now(timezone.utc)
    )

def test_synthesis_deploy_global(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("ML_SUPERIORITY_POLICY", "PASS"),
        _create_policy("CONFIDENCE_POLICY", "PASS"),
        _create_policy("COVERAGE_POLICY", "PASS")
    ]
    matrix = _create_matrix(evals)
    decision = synth.execute(matrix)
    
    assert decision.decision_state == "DEPLOY"
    assert decision.deployment_strategy == "GLOBAL"
    assert decision.selected_model == "PRIMARY"

def test_synthesis_deploy_pilot_coverage_fail(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("ML_SUPERIORITY_POLICY", "PASS"),
        _create_policy("CONFIDENCE_POLICY", "PASS"),
        _create_policy("COVERAGE_POLICY", "FAIL")
    ]
    matrix = _create_matrix(evals)
    decision = synth.execute(matrix)
    
    assert decision.decision_state == "DEPLOY"
    assert decision.deployment_strategy == "PILOT"
    
def test_synthesis_deploy_pilot_confidence_fail(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("ML_SUPERIORITY_POLICY", "PASS"),
        _create_policy("CONFIDENCE_POLICY", "FAIL"),
        _create_policy("COVERAGE_POLICY", "PASS")
    ]
    matrix = _create_matrix(evals)
    decision = synth.execute(matrix)
    
    assert decision.decision_state == "DEPLOY"
    assert decision.deployment_strategy == "PILOT"

def test_synthesis_retain(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("ML_SUPERIORITY_POLICY", "FAIL"),
        _create_policy("CONFIDENCE_POLICY", "PASS"),
        _create_policy("COVERAGE_POLICY", "PASS")
    ]
    matrix = _create_matrix(evals)
    decision = synth.execute(matrix)
    
    assert decision.decision_state == "RETAIN"
    assert decision.deployment_strategy == "NONE"
    assert decision.selected_model == "BASELINE"

def test_synthesis_suppressed(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("ML_SUPERIORITY_POLICY", "PASS"),
        _create_policy("CONFIDENCE_POLICY", "SUPPRESSED"),
        _create_policy("COVERAGE_POLICY", "PASS")
    ]
    matrix = _create_matrix(evals)
    decision = synth.execute(matrix)
    
    assert decision.decision_state == "NO_DECISION"
    assert decision.deployment_strategy == "NONE"

def test_synthesis_greenfield_deploy(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("ML_SUPERIORITY_POLICY", "NOT_APPLICABLE"),
        _create_policy("CONFIDENCE_POLICY", "PASS"), 
        _create_policy("COVERAGE_POLICY", "PASS")
    ]
    matrix = _create_matrix(evals)
    decision = synth.execute(matrix)
    
    assert decision.decision_state == "DEPLOY"
    assert decision.deployment_strategy == "GLOBAL"
    
def test_synthesis_greenfield_pilot(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("ML_SUPERIORITY_POLICY", "NOT_APPLICABLE"),
        _create_policy("CONFIDENCE_POLICY", "NOT_APPLICABLE"), 
        _create_policy("COVERAGE_POLICY", "FAIL")
    ]
    matrix = _create_matrix(evals)
    decision = synth.execute(matrix)
    
    assert decision.decision_state == "DEPLOY"
    assert decision.deployment_strategy == "PILOT"

def test_validator_empty_matrix(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    matrix = _create_matrix([])
    with pytest.raises(AnalyticsException) as exc:
        synth.execute(matrix)
    assert exc.value.error_code == "SYN-002"

def test_validator_duplicate_policy(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    evals = [
        _create_policy("POLICY_A", "PASS"),
        _create_policy("POLICY_A", "FAIL")
    ]
    matrix = _create_matrix(evals)
    with pytest.raises(AnalyticsException) as exc:
        synth.execute(matrix)
    assert exc.value.error_code == "SYN-003"
    
def test_validator_invalid_input(dummy_config):
    synth = DecisionSynthesizer(dummy_config)
    with pytest.raises(AnalyticsException) as exc:
        synth.execute(None)
    assert exc.value.error_code == "SYN-001"
