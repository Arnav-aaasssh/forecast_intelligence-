from typing import Optional, Dict
from .models import ReportSection, ChartDescriptor, EvidenceMetric, TraceabilityMetadata
from analytics.models import PerformanceEvidence, RecommendationEvidence, ExecutiveDecision

def build_q2_evaluation(
    all_performance: Dict[str, PerformanceEvidence],
    recommendation: RecommendationEvidence,
    decision: ExecutiveDecision
) -> ReportSection:
    """Builds the Q2 Forecast Model Evaluation section."""
    
    trace_meta = TraceabilityMetadata(
        source_layer="Content Engine",
        originating_contract_types=["PerformanceEvidence", "RecommendationEvidence", "ExecutiveDecision"]
    )
    
    scored_models = [k for k, v in all_performance.items() if v.status == "scored"]
    is_single_model = len(scored_models) == 1
    
    if is_single_model:
        return ReportSection(
            title="Model Champion Selection",
            business_question="Which forecasting model ranked first across all evaluated candidates?",
            observation="Only one model was evaluated.",
            traceability_metadata=trace_meta,
            primary_evidence=[
                EvidenceMetric(name="Models Scored", value="1")
            ],
            supporting_evidence=[],
            conclusion="No comparative ranking is possible.",
            decision_support="Champion selection requires at least 2 candidates.",
            recommendation=None,
            is_condensed=True,
            recommendation_suppressed=True,
            charts=[],
            tables=[],
            appendix_references=[]
        )

    top_model = recommendation.model_name
    composite = all_performance[top_model].composite_score
    scenario = decision.deployment_scenario.name
    
    # Calculate gap to runner-up
    scored_sorted = sorted(
        [(k, v) for k, v in all_performance.items() if v.status == "scored"],
        key=lambda x: x[1].composite_score, reverse=True
    )
    runner_up_name = scored_sorted[1][0] if len(scored_sorted) > 1 else None
    runner_up_score = scored_sorted[1][1].composite_score if runner_up_name else 0.0
    gap = composite - runner_up_score
    
    obs = f"Model {top_model} ranked #1 across {len(scored_models)} scored candidates with a composite score of {composite:.2f}/100."
    if runner_up_name:
        obs += f" It leads {runner_up_name} by {gap:.2f} points."
        
    conc = f"Model {top_model} achieved the highest composite score across all evaluated candidates."
    
    support = "The statistical champion has been identified. A narrow composite gap to the runner-up should be considered alongside switching costs."
    if recommendation.statistics.confidence_level.upper() == "LOW":
        support = "If confidence is Low, the champion ranking is reported for informational purposes only."
        
    suppress_rec = False
    if recommendation.statistics.confidence_level.upper() == "LOW" or decision.action == "Retain Incumbent":
        suppress_rec = True
        
    rec_text = decision.action if not suppress_rec else None

    charts = [
        ChartDescriptor(
            chart_type="horizontal_bar_chart",
            title="Model Composite Scores",
            data_references=["all_models_composite_scores"],
            description="Ranking of all evaluated models based on Winsorized Composite Score."
        )
    ]

    return ReportSection(
        title="Model Champion Selection",
        business_question="Which forecasting model ranked first across all evaluated candidates?",
        observation=obs,
        traceability_metadata=trace_meta,
        primary_evidence=[
            EvidenceMetric(name="Winsorized Composite Score", value=f"{composite:.2f}/100"),
            EvidenceMetric(name="WAPE", value=f"{all_performance[top_model].wape:.2%}"),
            EvidenceMetric(name="Weekly Win Rate", value=f"{recommendation.statistics.win_rate:.2%}" if recommendation.statistics.win_rate else "N/A")
        ],
        supporting_evidence=[
            EvidenceMetric(name="Absolute Bias", value=f"{all_performance[top_model].abs_bias:.2%}"),
            EvidenceMetric(name="IQR Stability", value=f"{all_performance[top_model].iqr_stability:.2%}"),
            EvidenceMetric(name="Hit10 Rate", value=f"{all_performance[top_model].hit10:.2%}"),
            EvidenceMetric(name="Runner-up Composite Score", value=f"{runner_up_score:.2f}/100"),
            EvidenceMetric(name="Total Models Scored", value=str(len(scored_models)))
        ],
        conclusion=conc,
        decision_support=support,
        recommendation=rec_text,
        is_condensed=False,
        recommendation_suppressed=suppress_rec,
        charts=charts,
        tables=[],
        appendix_references=["Appendix A: Full Model Scorecard Breakdown"]
    )
