import pandas as pd
import numpy as np
from .models import ComparisonEvidence, PerformanceEvidence

def generate_comparison_evidence(winner: PerformanceEvidence, runner_up: PerformanceEvidence, tied: bool) -> ComparisonEvidence:
    """Deterministically generates comparative flags between two models."""
    if tied:
        return ComparisonEvidence(better_wape=False, better_bias=False, better_stability=False, is_tied=True)
    
    w_wape, r_wape = winner.wape, runner_up.wape
    w_stab, r_stab = winner.iqr_stability, runner_up.iqr_stability
    w_bias, r_bias = winner.abs_bias, runner_up.abs_bias
    
    return ComparisonEvidence(
        better_wape=(w_wape < r_wape),
        better_bias=(w_bias < r_bias),
        better_stability=(w_stab < r_stab),
        is_tied=False
    )
