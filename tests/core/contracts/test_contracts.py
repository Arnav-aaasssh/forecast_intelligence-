import uuid
import pytest
from datetime import datetime
from dataclasses import asdict

from core.foundation.execution_context import ExecutionContext
from core.foundation.enums import Environment, ExecutionMode
from core.contracts.exceptions import ContractValidationException

from core.contracts.dataset import ValidatedDataset, DatasetReference
from core.contracts.analytics import AnalyticsResult
from core.contracts.decision import (
    DecisionBundle, Q1DecisionContract, Q2DecisionContract,
    Q3DecisionContract, Q4DecisionContract, ExecutiveDecisionContract
)
from core.contracts.content import ContentDocument, ContentSection
from core.contracts.rendered import RenderedDocument

@pytest.fixture
def execution_context():
    return ExecutionContext(
        run_id=uuid.uuid4(),
        correlation_id="corr-123",
        execution_timestamp=datetime.now(),
        platform_version="1.0.0",
        environment=Environment.PROD,
        execution_mode=ExecutionMode.API,
        user_id="user",
        request_source="postman",
        config_versions=(("decision", "v1"),),
        traceability_id=uuid.uuid4()
    )

def test_validated_dataset_valid(execution_context):
    dataset = ValidatedDataset(
        execution_context=execution_context,
        reference=DatasetReference(backend_type="LOCAL_CSV", uri="dummy"),
        schema_version="1.0",
        row_count=100,
        column_count=5,
        missing_values=0,
        time_series_count=10,
        data_hash="abc123hash"
    )
    assert dataset.row_count == 100
    assert hash(dataset)

def test_analytics_result_valid(execution_context):
    result = AnalyticsResult(
        execution_context=execution_context,
        run_hash="run-hash-99",
        global_wape=0.15,
        global_bias=0.02,
        segment_metrics=(("US", 0.12, 0.01), ("EU", 0.18, 0.03)),
        model_rankings=("ModelA", "ModelB"),
        warnings=()
    )
    assert result.global_wape == 0.15
    assert hash(result)
    assert asdict(result)["run_hash"] == "run-hash-99"

def test_decision_bundle_valid(execution_context):
    bundle = DecisionBundle(
        execution_context=execution_context,
        policy_version="1.0",
        decision_version="2.0",
        analytics_run_hash="hash",
        q1=Q1DecisionContract(primary_model="ModelA", is_retained=True, confidence_level="High"),
        q2=Q2DecisionContract(overall_health="Stable", degraded_segments=()),
        q3=Q3DecisionContract(forecastability_index="Medium", structural_breaks=0),
        q4=Q4DecisionContract(shock_detected=False, recovery_time=0),
        executive=ExecutiveDecisionContract(critical_warnings=0, requires_manual_intervention=False)
    )
    assert bundle.q1.primary_model == "ModelA"
    assert hash(bundle)
    assert asdict(bundle)["q1"]["primary_model"] == "ModelA"

def test_content_document_valid(execution_context):
    section = ContentSection(section_id="q1", title="Q1 Analysis", paragraphs=("Para 1", "Para 2"))
    doc = ContentDocument(
        execution_context=execution_context,
        decision_version="2.0",
        sections=(section,)
    )
    assert doc.sections[0].title == "Q1 Analysis"
    assert hash(doc)

def test_rendered_document_valid(execution_context):
    doc = RenderedDocument(
        execution_context=execution_context,
        mime_type="application/pdf",
        document_bytes=b"%PDF-1.4...",
        checksum="chksum",
        renderer_version="1.0",
        page_count=5
    )
    assert doc.page_count == 5
    assert hash(doc)

def test_immutability(execution_context):
    dataset = ValidatedDataset(
        execution_context=execution_context,
        reference=DatasetReference(backend_type="LOCAL_CSV", uri="dummy"),
        schema_version="1.0",
        row_count=100,
        column_count=5,
        missing_values=0,
        time_series_count=10,
        data_hash="abc123hash"
    )
    import dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        dataset.row_count = 200

def test_invalid_validation(execution_context):
    with pytest.raises(ContractValidationException):
        ValidatedDataset(
            execution_context=execution_context,
            reference=DatasetReference(backend_type="LOCAL_CSV", uri="dummy"),
            schema_version="1.0",
            row_count=-10,  # invalid
            column_count=5,
            missing_values=0,
            time_series_count=10,
            data_hash="abc123hash"
        )
