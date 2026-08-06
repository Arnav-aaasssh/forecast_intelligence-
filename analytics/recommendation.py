import pandas as pd
import numpy as np
from typing import Dict, Optional
from .models import ScorerConfig, RecommendationEvidence, ComparisonEvidence, PerformanceEvidence
from .policy import DecisionPolicy
from .stats_utils import compute_confidence
from .comparison import generate_comparison_evidence

def generate_recommendations(bt: pd.DataFrame, group_col: str, scored: Dict[str, PerformanceEvidence], config: ScorerConfig, policy: DecisionPolicy) -> Optional[RecommendationEvidence]:
    """
    Takes the leaderboard and determines the actual recommended model with evidence and confidence.
    Returns a strongly typed RecommendationEvidence object, or None if no valid models.
    """
    if not scored:
        return None

    valid_models = {k: v for k, v in scored.items() if v.status == "scored"}
    if not valid_models:
        return None
        
    ranked = sorted(valid_models.items(), key=lambda item: item[1].composite_score, reverse=True)
    
    if len(ranked) == 1:
        leader_name, leader_ev = ranked[0]
        return RecommendationEvidence(
            model_name=leader_name,
            is_top_scorer=True,
            is_statistical_winner=True,
            comparison=ComparisonEvidence(better_wape=True, better_bias=True, better_stability=True, is_tied=False),
            statistics=compute_confidence(pd.Series(dtype=float), pd.Series(dtype=float), config.sig_alpha, 0, config.min_wape_improvement)
        )
        
    def weekly_wape(name):
        sub = bt[bt[group_col] == name]
        return sub.groupby("Week_Ending").apply(
            lambda g: g["abs_err"].sum() / g["Actual_Offered"].sum() if g["Actual_Offered"].sum() else np.nan
        )
        
    leader_name, leader_ev = ranked[0]
    
    baseline_ev = valid_models.get(config.baseline_model)
    
    if leader_name == config.baseline_model:
        recommended_ev = leader_ev
        recommended_name = leader_name
        challenger_name, challenger_ev = ranked[1]
        tied_due_to_margin = False
    else:
        if baseline_ev is not None:
            challenger_ev = baseline_ev
            challenger_name = config.baseline_model
        else:
            challenger_name, challenger_ev = ranked[1]
            
        effect_size = challenger_ev.wape - leader_ev.wape
        weekly_rec = weekly_wape(leader_name)
        weekly_chal = weekly_wape(challenger_name)
        stat_evidence = compute_confidence(weekly_rec, weekly_chal, config.sig_alpha, effect_size, config.min_wape_improvement)
        
        conf_ranks = {"Low": 1, "Medium": 2, "High": 3}
        if baseline_ev is not None and conf_ranks.get(stat_evidence.confidence_level, 1) < conf_ranks.get(policy.min_confidence_to_switch, 2):
            recommended_ev = baseline_ev
            recommended_name = config.baseline_model
            challenger_ev = leader_ev 
            challenger_name = leader_name
            tied_due_to_margin = True
        else:
            recommended_ev = leader_ev
            recommended_name = leader_name
            tied_due_to_margin = False

    if recommended_name != leader_name or leader_name == config.baseline_model:
        effect_size = challenger_ev.wape - recommended_ev.wape
        weekly_rec = weekly_wape(recommended_name)
        weekly_chal = weekly_wape(challenger_name)
        stat_evidence = compute_confidence(weekly_rec, weekly_chal, config.sig_alpha, effect_size, config.min_wape_improvement)

    comp_evidence = generate_comparison_evidence(recommended_ev, challenger_ev, tied=tied_due_to_margin)
    
    return RecommendationEvidence(
        model_name=recommended_name,
        is_top_scorer=(recommended_name == leader_name),
        is_statistical_winner=True,
        comparison=comp_evidence,
        statistics=stat_evidence
    )
