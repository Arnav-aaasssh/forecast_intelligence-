import pytest
import uuid
import math
from datetime import datetime, timezone

from core.foundation.execution_context import ExecutionContext
from core.foundation.enums import Environment, ExecutionMode
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
from core.contracts.decision import DecisionContract
from core.contracts.content import BusinessQuestionContract, StructuredSection
from core.content.engine.orchestrator import ContentOrchestrator
from core.validation.exceptions import AnalyticsException
from core.contracts.exceptions import ContractValidationException

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

def _create_bundle(primary_wape=0.10, hit_rate=0.90, p_value=0.01, include_stats=True):
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
        
    stat_res = None
    if include_stats:
        stat_res = StatisticalAnalyticsResult(
            execution_context=ctx,
            primary_dataset_reference=ref,
            secondary_dataset_reference=ref,
            segment_statistics=(SegmentStatisticalMetrics("SEG1", 100, p_value, 0.5, True, "HIGH", None),),
            global_statistics=GlobalStatisticalMetrics(100, p_value, 0.5, True, "HIGH"),
            warnings=()
        )
        
    return AnalyticalEvidenceBundle(
        primary_evidence=ModelEvidence("MODEL_A", True, prim_acc, stat_res),
        secondary_evidence=None,
        execution_context=ctx,
        traceability_id=uuid.uuid4(),
        consolidation_timestamp=datetime.now(timezone.utc)
    )

def _create_decision(state="DEPLOY", strategy="GLOBAL", selected="PRIMARY"):
    return DecisionContract(
        decision_state=state,
        deployment_strategy=strategy,
        selected_model=selected,
        policy_evaluation_reference=(),
        decision_evaluation_reference=uuid.uuid4(),
        execution_context=_create_mock_context(),
        configuration_version="1.0",
        decision_timestamp=datetime.now(timezone.utc),
        traceability_id=uuid.uuid4(),
        version="1.0"
    )

def _create_bq_contract():
    return BusinessQuestionContract(
        business_question_id="Q1",
        primary_evidence_keys=("primary_wape",),
        supporting_evidence_keys=("p_value", "hit_rate"),
        observation_template="Model A has {primary_wape} WAPE and {hit_rate} hit rate.",
        conclusion_template="It is statistically significant at p={p_value}.",
        decision_support_template="Consider this for next cycle."
    )

def test_content_orchestrator_success():
    orchestrator = ContentOrchestrator()
    bundle = _create_bundle(primary_wape=0.10, hit_rate=0.90, p_value=0.01)
    decision = _create_decision("DEPLOY", "GLOBAL")
    bq = _create_bq_contract()
    
    section = orchestrator.execute(bq, decision, bundle)
    
    assert section.business_question_id == "Q1"
    assert section.observation == "Model A has 0.10 WAPE and 0.90 hit rate."
    assert section.conclusion == "It is statistically significant at p=0.01."
    assert section.decision_support == "Consider this for next cycle."
    assert section.recommendation == "DEPLOY"
    assert section.recommendation_suppressed is False
    assert len(section.primary_evidence) == 1
    assert len(section.supporting_evidence) == 2

def test_content_orchestrator_missing_evidence():
    orchestrator = ContentOrchestrator()
    bundle = _create_bundle(primary_wape=0.10, hit_rate=0.90, include_stats=False)
    decision = _create_decision("DEPLOY", "GLOBAL")
    bq = _create_bq_contract()
    
    section = orchestrator.execute(bq, decision, bundle)
    assert "p=N/A" in section.conclusion
    
def test_content_orchestrator_suppressed_decision():
    orchestrator = ContentOrchestrator()
    bundle = _create_bundle()
    decision = _create_decision("NO_DECISION", "NONE")
    bq = _create_bq_contract()
    
    section = orchestrator.execute(bq, decision, bundle, is_suppressed=True)
    assert section.recommendation == "NONE"
    assert section.recommendation_suppressed is True

def test_content_orchestrator_invalid_template():
    orchestrator = ContentOrchestrator()
    bundle = _create_bundle()
    decision = _create_decision()
    bq = BusinessQuestionContract(
        business_question_id="Q1",
        primary_evidence_keys=("primary_wape",),
        supporting_evidence_keys=(),
        observation_template="Missing {fake_metric}.",
        conclusion_template="test",
        decision_support_template="test"
    )
    
    with pytest.raises(AnalyticsException) as exc:
        orchestrator.execute(bq, decision, bundle)
    assert exc.value.error_code == "CON-001"

def test_content_orchestrator_invalid_inputs():
    orchestrator = ContentOrchestrator()
    with pytest.raises(AnalyticsException) as exc:
        orchestrator.execute(None, None, None)
    assert exc.value.error_code == "CON-003"
    
def test_structured_section_validation():
    with pytest.raises(ContractValidationException):
        StructuredSection(
            business_question_id="Q1",
            observation="",
            conclusion="",
            decision_support="",
            primary_evidence=(),
            supporting_evidence=(),
            recommendation="DEPLOY",
            recommendation_suppressed=True, 
            charts_referenced=(),
            execution_context_id="id",
            traceability_id="id",
            version="1.0"
        )
