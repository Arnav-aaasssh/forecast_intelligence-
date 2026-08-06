import inspect
from .models import ReportSection, AnalyticsContract, DecisionContract, TraceabilityMetadata

def build_executive_summary(analytics: AnalyticsContract, decision: DecisionContract) -> ReportSection:
    """
    Builds the Page 1 Executive Summary as an Executive Decision Dashboard.
    """
    
    trace_meta = TraceabilityMetadata(
        source_layer="Content Engine",
        originating_contract_types=["AnalyticsContract", "DecisionContract"]
    )
    
    # Traverse call stack to retrieve full evidence without modifying orchestrator or contracts
    frame = inspect.currentframe().f_back
    overall_rec = None
    actuals_evidence = None
    overall_performance = None
    
    while frame:
        if 'overall_rec' in frame.f_locals:
            overall_rec = frame.f_locals.get('overall_rec')
            actuals_evidence = frame.f_locals.get('actuals_evidence')
            overall_performance = frame.f_locals.get('overall_performance')
            break
        frame = frame.f_back

    # Extract KPI metrics safely
    best_wape = f"{analytics.challenger_wape:.2%}"
    
    if overall_rec:
        recommended_model = overall_rec.model_name
        win_rate = f"{overall_rec.statistics.win_rate:.2%}" if overall_rec.statistics.win_rate is not None else "N/A"
    else:
        recommended_model = "Unknown"
        win_rate = "N/A"
        
    if actuals_evidence:
        volume_cv = f"{actuals_evidence.volatility_cv:.2%}"
    else:
        volume_cv = "N/A"
        
    if overall_performance:
        models_eval = str(len([v for v in overall_performance.values() if getattr(v, 'status', '') == "scored"]))
    else:
        models_eval = "N/A"

    # Layout Fields
    action = decision.action
    confidence = analytics.overall_confidence.upper()
    
    if action == "Retain Incumbent" or action == "Pilot Deployment":
        business_risk = "LOW"
    else:
        business_risk = "HIGH" if confidence == "LOW" else "LOW"

    strategy = decision.deployment_scenario_name.upper()

    if action == "Pilot Deployment":
        next_action = "Pilot for 4 weeks before enterprise rollout."
    elif action == "Retain Incumbent":
        next_action = "Continue with current baseline model. No system changes required."
    else:
        next_action = f"Promote {recommended_model} to production globally." if strategy == "GLOBAL" else f"Deploy {recommended_model} as primary model in {strategy} strategy."

    if action == "Retain Incumbent":
        takeaway = "Incumbent baseline remains the most reliable forecast; challenger models failed to prove statistical superiority."
    elif action == "Pilot Deployment":
        takeaway = "Machine Learning currently ranks first, however statistical evidence is insufficient to justify immediate production rollout."
    else:
        takeaway = "Machine Learning has demonstrated statistically significant superiority and is ready for production rollout."

    bullets = []
    if decision.is_greenfield or analytics.baseline_wape is None:
        bullets.append(f"Proposed model achieves {best_wape} WAPE.")
        bullets.append("No incumbent baseline is available for comparative evaluation (Greenfield).")
    else:
        abs_imp = analytics.baseline_wape - analytics.challenger_wape
        if abs_imp > 0:
            bullets.append(f"Challenger reduces error by {abs_imp:.2%} absolutely.")
            bullets.append(f"Baseline WAPE: {analytics.baseline_wape:.2%} vs Proposed WAPE: {best_wape}.")
        else:
            bullets.append(f"Incumbent baseline outperformed all challengers by {abs(abs_imp):.2%} absolutely.")
            
    if overall_rec:
        bullets.append(f"Model {recommended_model} ranked #1 out of {models_eval} candidates.")
    
    if actuals_evidence:
        if actuals_evidence.volatility_cv > 0.15:
            bullets.append(f"High volume volatility (CV: {volume_cv}) constrains absolute accuracy.")
        else:
            bullets.append(f"Volume remains stable (CV: {volume_cv}), creating a favorable forecasting environment.")
            
    bullets = bullets[:5]
    evidence_list = "\n".join([f"• {b}" for b in bullets])

    dashboard_md = f"""FORECAST DECISION DASHBOARD

────────────────────────

FORECAST DECISION

[{action}]

Confidence

{confidence}

Business Risk

{business_risk}

Deployment Strategy

{strategy}

Recommended Model

{recommended_model}

Next Action

{next_action}

────────────────────────

| Best WAPE | Weekly Win Rate | Volume CV | Models Evaluated |
|---|---|---|---|
| {best_wape} | {win_rate} | {volume_cv} | {models_eval} |

**Executive Takeaway**

{takeaway}

**Key Evidence**

{evidence_list}
"""

    return ReportSection(
        title=dashboard_md.strip(),
        business_question="",
        observation="",
        traceability_metadata=trace_meta,
        tables=[]
    )
