import inspect
from typing import Optional
from .models import ReportSection, ChartDescriptor, Q1Contract, EvidenceMetric, TraceabilityMetadata

def build_q1_assessment(contract: Q1Contract) -> ReportSection:
    """Builds the Q1 Manual vs ML Assessment section."""
    
    trace_meta = TraceabilityMetadata(
        source_layer="Content Engine",
        originating_contract_types=["Q1Contract"]
    )
    
    if not contract.has_baseline:
        return ReportSection(
            title="Accuracy Assessment (Incumbent vs ML)",
            business_question="Did human planners or machine learning algorithms produce more accurate forecasts?",
            observation="No incumbent baseline is available for comparison (Greenfield scenario).",
            traceability_metadata=trace_meta,
            primary_evidence=[
                EvidenceMetric(name="Baseline Availability", value="False")
            ],
            supporting_evidence=[],
            conclusion="No incumbent baseline is available for comparison (Greenfield).",
            decision_support="The ML model establishes the initial operational baseline for future comparison.",
            recommendation=None,
            is_condensed=True,
            recommendation_suppressed=True,
            charts=[],
            tables=[],
            appendix_references=[]
        )
        
    delta = abs(contract.manual_wape - contract.ml_wape)
    
    # Conclusion and Observation logic
    if contract.ml_won and delta >= 0.015:
        obs = f"ML outperformed the incumbent baseline by {delta:.2%} WAPE."
        conc = f"ML reduces forecast error by {delta:.2%} relative to the incumbent baseline."
        support = "The accuracy delta should be considered alongside operational switching costs when evaluating migration."
    elif not contract.ml_won and delta >= 0.015:
        obs = f"The incumbent baseline outperformed ML by {delta:.2%} WAPE."
        conc = "The incumbent baseline remains more accurate than all evaluated ML models."
        support = "Accuracy evidence does not support model migration at this time."
    else:
        obs = f"ML and the incumbent baseline performed within statistical noise (Δ {delta:.2%})."
        conc = "No statistically meaningful difference exists between incumbent and challenger."
        support = "Accuracy evidence does not compel migration; alternative factors (maintenance, scale) must drive the decision."
        
    charts = [
        ChartDescriptor(
            chart_type="bar_chart",
            title="WAPE Comparison: Manual vs ML",
            data_references=["manual_wape", "ml_wape"],
            description="Side-by-side comparison of overall absolute error."
        )
    ]
    
    suppress_rec = False
    if contract.confidence_level.upper() == "LOW" or delta < 0.015:
        suppress_rec = True
        
    rec_text = contract.action_recommendation if not suppress_rec else None

    return ReportSection(
        title="Accuracy Assessment (Incumbent vs ML)",
        business_question="Did human planners or machine learning algorithms produce more accurate forecasts?",
        observation=obs,
        traceability_metadata=trace_meta,
        primary_evidence=[
            EvidenceMetric(name="ML Overall WAPE", value=f"{contract.ml_wape:.2%}"),
            EvidenceMetric(name="Manual Overall WAPE", value=f"{contract.manual_wape:.2%}"),
            EvidenceMetric(name="Absolute Improvement Delta", value=f"{delta:.2%}")
        ],
        supporting_evidence=[
            EvidenceMetric(name="Confidence Level", value=contract.confidence_level)
        ],
        conclusion=conc,
        decision_support=support,
        recommendation=rec_text,
        is_condensed=False,
        recommendation_suppressed=suppress_rec,
        charts=charts,
        tables=[],
        appendix_references=[]
    )
