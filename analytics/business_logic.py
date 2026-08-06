import pandas as pd
from typing import Dict, List, Optional
from .models import BusinessImpact, DeploymentScenario, ExecutiveDecision, RecommendationEvidence
from .policy import DecisionPolicy

def evaluate_business_impact(baseline_wape: Optional[float], challenger_wape: float, policy: DecisionPolicy) -> BusinessImpact:
    """Calculates deterministic business impact based on Policy thresholds."""
    if baseline_wape is None or pd.isna(baseline_wape):
        # Greenfield deployment scenario
        return BusinessImpact(
            baseline_wape=None,
            challenger_wape=challenger_wape,
            abs_improvement=None,
            rel_improvement=None,
            impact_rating="High",  # Greenfield is typically considered high-impact if it replaces nothing
            is_greenfield=True
        )
        
    abs_imp = baseline_wape - challenger_wape
    rel_imp = abs_imp / baseline_wape if baseline_wape else 0
    
    if abs_imp >= policy.impact_high_abs or rel_imp >= policy.impact_high_rel:
        rating = "High"
    elif abs_imp >= policy.impact_med_abs or rel_imp >= policy.impact_med_rel:
        rating = "Medium"
    else:
        rating = "Low"
        
    return BusinessImpact(
        baseline_wape=baseline_wape,
        challenger_wape=challenger_wape,
        abs_improvement=abs_imp,
        rel_improvement=rel_imp,
        impact_rating=rating,
        is_greenfield=False
    )

def _get_complexity(num_models: int, policy: DecisionPolicy) -> str:
    if num_models <= policy.max_models_low_complexity:
        return "Low"
    elif num_models <= policy.max_models_medium_complexity:
        return "Medium"
    else:
        return "High"

def build_deployment_scenarios(bt: pd.DataFrame, overall_winner: RecommendationEvidence, region_winners: Dict[str, RecommendationEvidence], channel_winners: Dict[str, RecommendationEvidence], policy: DecisionPolicy) -> List[DeploymentScenario]:
    """Generates the three deployment scenarios: Global, Regional, Segmented (Channel)"""
    scenarios = []
    
    def get_blended_wape(model_map: Dict[str, str], segment_col: str) -> float:
        total_err = 0
        total_actual = 0
        
        if segment_col == "Overall":
            model = model_map["Overall"]
            sub = bt[bt["Model"] == model]
            total_err = sub["abs_err"].sum()
            total_actual = sub["Actual_Offered"].sum()
        else:
            for seg, model in model_map.items():
                sub = bt[(bt[segment_col] == seg) & (bt["Model"] == model)]
                total_err += sub["abs_err"].sum()
                total_actual += sub["Actual_Offered"].sum()
                
        return total_err / total_actual if total_actual else 0
        
    # Scenario A: Global
    wape_global = get_blended_wape({"Overall": overall_winner.model_name}, "Overall")
    scenarios.append(DeploymentScenario(
        name="Global",
        models_required=1,
        complexity_rating=_get_complexity(1, policy),
        blended_wape=wape_global
    ))
    
    # Scenario B: Regional
    wape_reg = get_blended_wape({r: w.model_name for r, w in region_winners.items()}, "Region")
    scenarios.append(DeploymentScenario(
        name="Regional",
        models_required=len(region_winners),
        complexity_rating=_get_complexity(len(region_winners), policy),
        blended_wape=wape_reg
    ))
    
    # Scenario C: Segmented (Channel)
    wape_chan = get_blended_wape({c: w.model_name for c, w in channel_winners.items()}, "Channel")
    scenarios.append(DeploymentScenario(
        name="Segmented",
        models_required=len(channel_winners),
        complexity_rating=_get_complexity(len(channel_winners), policy),
        blended_wape=wape_chan
    ))
    
    return scenarios

def make_executive_decision(bt: pd.DataFrame, overall_winner: RecommendationEvidence, region_winners: Dict[str, RecommendationEvidence], channel_winners: Dict[str, RecommendationEvidence], policy: DecisionPolicy, baseline_model: str) -> ExecutiveDecision:
    """Executes the final Decision Matrix based on configured Policy."""
    # Get baseline WAPE
    baseline_sub = bt[bt["Model"] == baseline_model]
    if baseline_sub.empty or baseline_sub["Actual_Offered"].sum() == 0:
        baseline_wape = None
    else:
        baseline_wape = baseline_sub["abs_err"].sum() / baseline_sub["Actual_Offered"].sum()
    
    # 2. Build Scenarios
    scenarios = build_deployment_scenarios(bt, overall_winner, region_winners, channel_winners, policy)
    scen_global = next(s for s in scenarios if s.name == "Global")
    scen_reg = next(s for s in scenarios if s.name == "Regional")
    scen_seg = next(s for s in scenarios if s.name == "Segmented")
    
    # 3. Select Scenario based on Policy Thresholds
    selected_scenario = scen_global
    reasoning = f"Global model {overall_winner.model_name} selected to minimize MLOps complexity."
    
    if (scen_global.blended_wape - scen_reg.blended_wape) >= policy.regional_min_improvement_abs:
        selected_scenario = scen_reg
        reasoning = f"Regional segmentation selected because it improves WAPE by >{policy.regional_min_improvement_abs*100:.1f}% over Global, justifying {scen_reg.complexity_rating} complexity."
        
    if (selected_scenario.blended_wape - scen_seg.blended_wape) >= policy.segmented_min_improvement_abs:
        selected_scenario = scen_seg
        reasoning = f"Deep segmentation selected because it improves WAPE by >{policy.segmented_min_improvement_abs*100:.1f}% over Regional, justifying {scen_seg.complexity_rating} complexity."
        
    selected_scenario.selected = True
    
    # 4. Assess Impact
    impact = evaluate_business_impact(baseline_wape, selected_scenario.blended_wape, policy)
    
    # 5. Final Matrix
    action = "Retain Incumbent"
    overall_conf = overall_winner.statistics.confidence_level
    
    if overall_winner.model_name == baseline_model:
        action = "Retain Incumbent"
        reasoning = "The incumbent baseline is the statistical winner. No migration necessary."
    elif impact.is_greenfield:
        if overall_conf in ["Medium", "High"]:
            action = "Full Global Switch" if selected_scenario.name == "Global" else "Segmented Switch"
            reasoning = f"Incumbent Baseline Unavailable. Greenfield deployment of {selected_scenario.name} strategy recommended due to {overall_conf} statistical confidence."
        else:
            action = "Pilot Deployment"
            reasoning = f"Incumbent Baseline Unavailable. However, statistical confidence is Low. Recommend a pilot deployment of the {selected_scenario.name} strategy."
    elif impact.impact_rating == "Low" or overall_conf == "Low":
        action = "Retain Incumbent"
        reasoning = f"Despite statistical gains, confidence is {overall_conf} and business impact is {impact.impact_rating}. The ROI does not justify switching."
    elif impact.impact_rating == "Medium":
        action = "Pilot Deployment"
        reasoning = f"Business impact is Medium with {overall_conf} confidence. Recommend a pilot of the {selected_scenario.name} strategy."
    else:
        if selected_scenario.name == "Global":
            action = "Full Global Switch"
        else:
            action = "Segmented Switch"
            
    return ExecutiveDecision(
        action=action,
        business_impact=impact,
        deployment_scenario=selected_scenario,
        all_scenarios=scenarios,
        reasoning=reasoning
    )
