from typing import Dict, Optional
from .models import ReportSection, ReportTable, TraceabilityMetadata
from analytics.models import PerformanceEvidence, RecommendationEvidence, ActualsAnalysis

def build_appendix(
    all_scores: Dict[str, PerformanceEvidence],
    recommendation: Optional[RecommendationEvidence] = None,
    actuals: Optional[ActualsAnalysis] = None
) -> ReportSection:
    """Builds the strictly audit-focused Appendix section."""
    
    trace_meta = TraceabilityMetadata(
        source_layer="Content Engine",
        originating_contract_types=["PerformanceEvidence", "RecommendationEvidence", "ActualsAnalysis"]
    )
    
    # Table 1: Model Scorecard (Normalization results)
    score_rows = []
    excluded_rows = []
    
    sorted_scores = sorted(all_scores.items(), key=lambda item: item[1].composite_score, reverse=True)
    
    for model, evidence in sorted_scores:
        if evidence.status == "scored":
            score_rows.append([
                model, 
                f"{evidence.composite_score:.2f}", 
                f"{evidence.wape:.2%}", 
                f"{evidence.abs_bias:.2%}", 
                f"{evidence.iqr_stability:.2%}", 
                f"{evidence.hit10:.2%}"
            ])
        else:
            excluded_rows.append([model, evidence.status, "Failed heuristic or volume constraints"])
            
    score_table = ReportTable(
        headers=["Model", "Composite Score", "WAPE", "Abs Bias", "Stability IQR", "Hit10"],
        rows=score_rows
    )
    
    tables = [score_table]
    
    if excluded_rows:
        tables.append(ReportTable(
            headers=["Excluded Model", "Status", "Reason"],
            rows=excluded_rows
        ))
        
    # Table 2: Statistical Evidence (P-values, Win Rates)
    if recommendation:
        p_val = recommendation.statistics.p_value
        win_rate = recommendation.statistics.win_rate
        stats_rows = [
            ["Confidence Level", recommendation.statistics.confidence_level],
            ["P-Value (Wilcoxon)", f"{p_val:.4f}" if p_val is not None and not (isinstance(p_val, float) and p_val != p_val) else "N/A"],
            ["Weekly Win Rate", f"{win_rate:.2%}" if win_rate is not None and not (isinstance(win_rate, float) and win_rate != win_rate) else "N/A"]
        ]
        tables.append(ReportTable(
            headers=["Statistical Test", "Result"],
            rows=stats_rows
        ))
        
    # Table 3: Data Quality
    if actuals:
        quality_rows = [
            ["Coefficient of Variation", f"{actuals.volatility_cv:.2%}"],
            ["Identified Anomalies", str(len(actuals.anomalies))],
            ["Trend Direction", actuals.trend]
        ]
        tables.append(ReportTable(
            headers=["Data Quality Metric", "Value"],
            rows=quality_rows
        ))
    
    return ReportSection(
        title="Appendix A: Statistical & Data Audit",
        business_question="What are the underlying statistical proofs for this document?",
        observation="",
        traceability_metadata=trace_meta,
        conclusion="See attached tables for full statistical, normalization, and exclusion audit.",
        recommendation=None,
        is_condensed=False,
        recommendation_suppressed=True,
        tables=tables
    )
