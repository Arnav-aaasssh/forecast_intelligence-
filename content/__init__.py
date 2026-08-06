from .models import ReportSection, ReportTable, ContentContract
from .executive_builder import build_executive_summary
from .q1_builder import build_q1_assessment
from .q2_builder import build_q2_evaluation
from .q3_builder import build_q3_actuals
from .q4_builder import build_q4_drivers
from .appendix_builder import build_appendix

def generate_report_content(analytics_evidence: dict, decision_contract: dict) -> ReportDocument:
    """Orchestrates the construction of the full report document structure."""
    
    has_baseline = analytics_evidence.get('has_baseline', True)
    
    q1 = build_q1_assessment(analytics_evidence, decision_contract, has_baseline)
    q2 = build_q2_evaluation(analytics_evidence, decision_contract)
    q3 = build_q3_actuals(analytics_evidence, decision_contract)
    q4 = build_q4_drivers(analytics_evidence, decision_contract)
    exec_summary = build_executive_summary(decision_contract)
    appx = build_appendix(analytics_evidence)
    
    return ReportDocument(
        executive_summary=exec_summary,
        q1_assessment=q1,
        q2_evaluation=q2,
        q3_actuals=q3,
        q4_drivers=q4,
        appendix=appx
    )
