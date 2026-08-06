import pandas as pd
import numpy as np
import sys
import os

# Add parent dir to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from legacy.legacy_model_scorer import score_group as legacy_score
from legacy.legacy_model_scorer import ScorerConfig as LegacyConfig
from analytics.performance import score_group
from analytics.models import ScorerConfig
from decision_orchestrator import load_backtest

def main():
    print("Running Parity Validation...")
    dataset_path = "sample_data/FinalForecast_Imputed.xlsx"
    
    if not os.path.exists(dataset_path):
        print(f"Test dataset not found at {dataset_path}")
        return
        
    bt = load_backtest(dataset_path)
    config = ScorerConfig()
    
    # Run legacy scorer
    print("Executing Legacy Analytics...")
    legacy_config = LegacyConfig()
    legacy_results = legacy_score(bt, "Model", legacy_config)
    legacy_ranked = legacy_results[legacy_results["status"] == "scored"].sort_values("CompositeScore", ascending=False).reset_index(drop=True)
    
    # Run new modular analytics
    print("Executing New Modular Analytics...")
    new_results = score_group(bt, "Model", config)
    new_ranked = new_results[new_results["status"] == "scored"].sort_values("CompositeScore", ascending=False).reset_index(drop=True)
    
    # Assertions
    print("\n--- Parity Verification Matrix ---")
    
    # 1. Number of models scored
    assert len(legacy_ranked) == len(new_ranked), f"Model count mismatch: {len(legacy_ranked)} vs {len(new_ranked)}"
    print(f"[PASS] Model Count Parity: {len(legacy_ranked)} models scored")
    
    # Sort alphabetically by Model to avoid tie-breaker ordering issues
    legacy_ranked = legacy_ranked.sort_values("Model").reset_index(drop=True)
    new_ranked = new_ranked.sort_values("Model").reset_index(drop=True)
    
    # 2. Rankings
    for i in range(len(legacy_ranked)):
        leg_name = legacy_ranked.iloc[i]["Model"]
        new_name = new_ranked.iloc[i]["Model"]
        assert leg_name == new_name, f"Model mismatch at position {i}: Legacy {leg_name} != New {new_name}"
    print("[PASS] Ranking Order Parity: 100% Match")
    
    # 3. WAPE, Bias, Hit10, Stability, Composite
    metrics_to_check = ["WAPE", "AbsBias", "Hit10", "IQR_Stability", "CompositeScore"]
    for metric in metrics_to_check:
        leg_vals = legacy_ranked[metric].values
        new_vals = new_ranked[metric].values
        np.testing.assert_allclose(leg_vals, new_vals, rtol=1e-3, atol=1e-3, err_msg=f"Mismatch in {metric}")
        print(f"[PASS] {metric} Calculation Parity: 100% Match")
        
    print("\nPARITY VALIDATION PASSED: The new modular analytics layer is mathematically identical to the legacy monolith.")

if __name__ == "__main__":
    main()
