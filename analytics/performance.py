import pandas as pd
import numpy as np
from typing import Dict, List
from .models import ScorerConfig, PerformanceEvidence
from .stats_utils import normalize_absolute

def raw_metrics(g: pd.DataFrame, hit_band: float) -> pd.Series:
    """Compute raw performance metrics for a forecast group."""
    pct_err_clean = g["pct_err"].replace([np.inf, -np.inf], np.nan)
    denom = g["Actual_Offered"].sum()
    wape = g["abs_err"].sum() / denom if denom else np.nan
    bias = g["err"].sum() / denom if denom else np.nan
    q75, q25 = pct_err_clean.quantile(0.75), pct_err_clean.quantile(0.25)
    
    return pd.Series({
        "n_rows": len(g),
        "n_weeks": g["Week_Ending"].nunique(),
        "WAPE": wape,
        "AbsBias": abs(bias),
        "StdErrPct": pct_err_clean.std(),
        "IQR_Stability": q75 - q25,
        "Hit10": (pct_err_clean.abs() <= hit_band).mean(),
    })

def score_group(bt: pd.DataFrame, group_col: str, config: ScorerConfig) -> Dict[str, PerformanceEvidence]:
    """
    Computes absolute metrics and Winsorized composite scores for all models in a group.
    Returns a dictionary of strongly typed PerformanceEvidence objects mapped by model name.
    """
    if bt.empty:
        return {}
        
    metrics = bt.groupby(group_col).apply(lambda g: raw_metrics(g, config.hit_band)).reset_index()
    
    # Filter out models with insufficient history
    metrics["status"] = "scored"
    metrics.loc[metrics["n_rows"] < config.min_rows, "status"] = f"insufficient data (<{config.min_rows} rows)"
    
    scored = metrics[metrics["status"] == "scored"].copy()
    if not scored.empty:
        # Apply Winsorized Min-Max Normalization (absolute bounds)
        s_wape = normalize_absolute(scored["WAPE"], *config.wape_bounds)
        s_bias = normalize_absolute(scored["AbsBias"], *config.bias_bounds)
        s_stab = normalize_absolute(scored["IQR_Stability"], *config.stab_bounds)
        s_hit10 = normalize_absolute(scored["Hit10"], *config.hit10_bounds)
        
        scored["CompositeScore"] = (
            config.weights["WAPE"] * s_wape
            + config.weights["Hit10"] * s_hit10
            + config.weights["Bias"] * s_bias
            + config.weights["Stability"] * s_stab
        ) * 100
    else:
        scored["CompositeScore"] = np.nan
        
    final = pd.concat([scored, metrics[metrics["status"] != "scored"]])
    
    results = {}
    for _, row in final.iterrows():
        model_name = str(row[group_col])
        results[model_name] = PerformanceEvidence(
            n_rows=int(row["n_rows"]),
            n_weeks=int(row["n_weeks"]),
            wape=float(row["WAPE"]),
            abs_bias=float(row["AbsBias"]),
            std_err_pct=float(row.get("StdErrPct", 0.0) if pd.notna(row.get("StdErrPct")) else 0.0),
            iqr_stability=float(row["IQR_Stability"]),
            hit10=float(row["Hit10"]),
            composite_score=float(row.get("CompositeScore", 0.0) if pd.notna(row.get("CompositeScore")) else 0.0),
            status=str(row["status"])
        )
        
    return results
