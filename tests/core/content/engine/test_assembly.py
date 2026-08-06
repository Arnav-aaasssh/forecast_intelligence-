import pytest
import uuid
from datetime import datetime, timezone
from core.contracts.content import StructuredSection, ReportDocument, ReportMetadata
from core.content.engine.assembly import SectionOrdering, ReportAssemblyEngine
from core.validation.exceptions import AnalyticsException
from core.contracts.exceptions import ContractValidationException

def _create_section(bq_id, exec_id, trace_id, charts=()):
    return StructuredSection(
        business_question_id=bq_id,
        observation="Obs",
        conclusion="Conc",
        decision_support="DS",
        primary_evidence=(),
        supporting_evidence=(),
        recommendation="NONE",
        recommendation_suppressed=True,
        charts_referenced=charts,
        execution_context_id=exec_id,
        traceability_id=trace_id,
        version="1.0"
    )

def test_assembly_engine_success():
    exec_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    s1 = _create_section("Q1", exec_id, trace_id, ("chart_a",))
    s2 = _create_section("Q2", exec_id, trace_id, ("chart_b",))
    s3 = _create_section("Q3", exec_id, trace_id)
    
    ordering = SectionOrdering(order_config=("Q1", "Q2", "Q3", "Q4"), mandatory_sections=("Q1", "Q2"))
    engine = ReportAssemblyEngine(ordering)
    
    doc = engine.assemble((s3, s1, s2), "Test Report", "Exec Summary")
    
    assert doc.metadata.title == "Test Report"
    assert doc.sections[0].business_question_id == "Q1"
    assert doc.sections[1].business_question_id == "Q2"
    assert doc.sections[2].business_question_id == "Q3"
    assert "chart_a" in doc.assets
    assert "chart_b" in doc.assets

def test_assembly_engine_missing_mandatory():
    exec_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    s1 = _create_section("Q1", exec_id, trace_id)
    s3 = _create_section("Q3", exec_id, trace_id)
    
    ordering = SectionOrdering(order_config=("Q1", "Q2", "Q3", "Q4"), mandatory_sections=("Q1", "Q2"))
    engine = ReportAssemblyEngine(ordering)
    
    with pytest.raises(AnalyticsException) as exc:
        engine.assemble((s1, s3), "Test Report", "Exec Summary")
    assert exc.value.error_code == "ASM-002"
    
def test_assembly_engine_duplicate_section():
    exec_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    s1 = _create_section("Q1", exec_id, trace_id)
    s1_dup = _create_section("Q1", exec_id, trace_id)
    
    ordering = SectionOrdering(order_config=("Q1", "Q2", "Q3", "Q4"), mandatory_sections=("Q1",))
    engine = ReportAssemblyEngine(ordering)
    
    with pytest.raises(AnalyticsException) as exc:
        engine.assemble((s1, s1_dup), "Test Report", "Exec Summary")
    assert exc.value.error_code == "ASM-001"

def test_assembly_engine_traceability_mismatch():
    exec_id1 = str(uuid.uuid4())
    exec_id2 = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    s1 = _create_section("Q1", exec_id1, trace_id)
    s2 = _create_section("Q2", exec_id2, trace_id)
    
    ordering = SectionOrdering(order_config=("Q1", "Q2", "Q3", "Q4"), mandatory_sections=("Q1",))
    engine = ReportAssemblyEngine(ordering)
    
    with pytest.raises(AnalyticsException) as exc:
        engine.assemble((s1, s2), "Test Report", "Exec Summary")
    assert exc.value.error_code == "ASM-004"

def test_report_document_immutability():
    metadata = ReportMetadata("Title", "Sum", "2026", "1.0")
    doc = ReportDocument("exec", "trace", metadata, (), (), ())
    
    with pytest.raises(Exception):
        doc.execution_context_id = "new"

def test_report_document_validation():
    metadata = ReportMetadata("Title", "Sum", "2026", "1.0")
    with pytest.raises(ContractValidationException):
        ReportDocument(123, "trace", metadata, (), (), ())
