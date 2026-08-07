import pandas as pd
import numpy as np
import argparse

# Layer 1: Configuration (Technically outside the pipeline)
from analytics.models import ScorerConfig
from analytics.policy import DecisionPolicy

# Layer 2: Analytics
from analytics.actuals import analyze_actuals
from analytics.performance import score_group
from analytics.recommendation import generate_recommendations
from analytics.degradation import associate_degradation

# Layer 3: Decision Intelligence
from analytics.business_logic import make_executive_decision

# Layer 4: Content
from content.models import ContentContract
from content.executive_builder import build_executive_summary
from content.q1_builder import build_q1_assessment
from content.q2_builder import build_q2_evaluation
from content.q3_builder import build_q3_actuals
from content.q4_builder import build_q4_drivers
from content.appendix_builder import build_appendix

# Layer 5: Presentation
from analytics.report_generator import generate_report

def load_backtest(path: str) -> pd.DataFrame:
    """Data Validation Layer: Load and validate the dataset schema."""
    df = pd.read_excel(path)
    required = {"ML_Forecast", "Actual_Offered", "Model", "Family", "Week_Ending"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    bt = df[df["Actual_Offered"].notna()].copy()
    if bt.empty:
        raise ValueError("No backtested rows found.")

    # Data enrichment for downstream layers
    bt["err"] = bt["ML_Forecast"] - bt["Actual_Offered"]
    bt["abs_err"] = bt["err"].abs()
    with np.errstate(divide="ignore", invalid="ignore"):
        bt["pct_err"] = bt["err"] / bt["Actual_Offered"]
        
    bt["Overall"] = "Overall"
    return bt

def run_analysis(dataset_path: str, out_md: str, out_pdf: str):
    """
    Pure Orchestrator:
    Executes the 5-layer pipeline strictly by passing strongly-typed contracts.
    """
    # ---------------------------------------------------------
    # Layer 1: Data Validation
    # ---------------------------------------------------------
    bt = load_backtest(dataset_path)
    config = ScorerConfig()
    policy = DecisionPolicy()

    # ---------------------------------------------------------
    # Layer 2: Analytics (Deterministic Computation)
    # ---------------------------------------------------------
    actuals_evidence = analyze_actuals(bt)

    overall_performance = score_group(bt, "Model", config)
    overall_rec = generate_recommendations(bt, "Model", overall_performance, config, policy)

    def get_segment_winners(segment_col: str):
        winners = {}
        if segment_col in bt.columns:
            for seg_val in bt[segment_col].dropna().unique():
                seg_bt = bt[bt[segment_col] == seg_val].copy()
                seg_perf = score_group(seg_bt, "Model", config)
                rec = generate_recommendations(seg_bt, "Model", seg_perf, config, policy)
                if rec:
                    winners[seg_val] = rec
        return winners

    region_winners = get_segment_winners("Region")
    channel_winners = get_segment_winners("Channel")

    degradations = []
    if overall_rec:
        degradations = associate_degradation(bt, overall_rec.model_name, actuals_evidence.anomalies)

    # ---------------------------------------------------------
    # Layer 3: Decision Intelligence (Policy Application)
    # ---------------------------------------------------------
    if not overall_rec:
        raise ValueError("No valid models found to recommend.")
        
    exec_decision = make_executive_decision(
        bt=bt, 
        overall_winner=overall_rec, 
        region_winners=region_winners, 
        channel_winners=channel_winners, 
        policy=policy, 
        baseline_model=config.baseline_model
    )

    # ---------------------------------------------------------
    # Layer 4: Content Generation (Evidence Transformation)
    # ---------------------------------------------------------
    
    from content.models import AnalyticsContract, DecisionContract, Q1Contract
    
    analytics_contract = AnalyticsContract(
        overall_confidence=overall_rec.statistics.confidence_level,
        baseline_wape=exec_decision.business_impact.baseline_wape,
        challenger_wape=exec_decision.business_impact.challenger_wape
    )
    
    decision_contract = DecisionContract(
        action=exec_decision.action,
        deployment_scenario_name=exec_decision.deployment_scenario.name,
        is_greenfield=exec_decision.business_impact.is_greenfield
    )
    
    exec_summary = build_executive_summary(analytics_contract, decision_contract)

    # Q1 Map
    has_baseline = config.baseline_model in bt["Model"].values
    baseline_ev = overall_performance.get(config.baseline_model)
    ml_wape = overall_rec.wape if hasattr(overall_rec, 'wape') else overall_performance[overall_rec.model_name].wape
    manual_wape = baseline_ev.wape if baseline_ev else 0.0

    q1_contract = Q1Contract(
        has_baseline=has_baseline,
        manual_wape=manual_wape,
        ml_wape=ml_wape,
        ml_won=overall_rec.model_name != config.baseline_model,
        confidence_level=overall_rec.statistics.confidence_level,
        action_recommendation=exec_decision.action
    )
    q1_assessment = build_q1_assessment(q1_contract)

    # Q2 Map
    q2_evaluation = build_q2_evaluation(
        all_performance=overall_performance,
        recommendation=overall_rec,
        decision=exec_decision
    )

    # Q3 Map
    q3_actuals = build_q3_actuals(actuals_evidence)

    # Q4 Map
    q4_drivers = build_q4_drivers(
        anomalies_count=len(actuals_evidence.anomalies),
        degradations=degradations
    )

    # Appendix Map
    appendix_section = build_appendix(
        all_scores=overall_performance,
        recommendation=overall_rec,
        actuals=actuals_evidence
    )

    # Compile Document
    doc = ContentContract(
        executive_summary=exec_summary,
        q1_assessment=q1_assessment,
        q2_evaluation=q2_evaluation,
        q3_actuals=q3_actuals,
        q4_drivers=q4_drivers,
        appendix=appendix_section
    )

    # ---------------------------------------------------------
    # Layer 5: Presentation (Rendering)
    # ---------------------------------------------------------
    generate_report(doc, out_md)
    from analytics.pdf_renderer import generate_pdf
    generate_pdf(out_md, out_pdf)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="Path to backtest excel file")
    parser.add_argument("--out_md", default="reports/Forecast_Decision_Report.md")
    parser.add_argument("--out_pdf", default="reports/Forecast_Decision_Report.pdf")
    args = parser.parse_args()
    
    run_analysis(args.dataset, args.out_md, args.out_pdf)
