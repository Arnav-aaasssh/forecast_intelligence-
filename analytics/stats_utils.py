import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
from .models import StatisticalEvidence

def normalize_absolute(s: pd.Series, best: float, worst: float) -> pd.Series:
    """
    Winsorized Min-Max normalization using business thresholds.
    Scores reflect absolute performance, solving the IIA violation.
    """
    if best < worst:
        clipped = s.clip(best, worst)
        return (worst - clipped) / (worst - best)
    else:
        clipped = s.clip(worst, best)
        return (clipped - worst) / (best - worst)

def compute_confidence(series_a: pd.Series, series_b: pd.Series, alpha: float, effect_size: float, min_effect: float) -> StatisticalEvidence:
    """
    Computes statistical and business confidence between two weekly WAPE series.
    Returns strongly typed StatisticalEvidence.
    """
    common = series_a.index.intersection(series_b.index)
    if len(common) < 5:
        return StatisticalEvidence("Low", np.nan, np.nan)
    
    # Positive if A is better (lower WAPE)
    diff = series_b[common] - series_a[common]
    win_rate = float((diff > 0).mean())
    
    try:
        stat, p = wilcoxon(series_a[common], series_b[common])
    except ValueError:
        p = np.nan
        
    if pd.isna(p):
        return StatisticalEvidence("Low", np.nan, win_rate)
        
    # High confidence: Statistically significant AND consistent wins AND sufficient effect size
    if p < alpha and win_rate >= 0.6 and effect_size >= min_effect:
        return StatisticalEvidence("High", p, win_rate)
    # Medium confidence: (Marginally significant OR highly consistent) AND sufficient effect size
    elif (p < 0.15 or win_rate >= 0.7) and effect_size >= (min_effect / 2):
        return StatisticalEvidence("Medium", p, win_rate)
    else:
        return StatisticalEvidence("Low", p, win_rate)
