"""
model_scorer.py — Decision Intelligence Engine for Model Selection

Evaluates forecast performance and produces a deterministic evidence-based 
recommendation for which model/family should be selected by the planning manager.

Key Improvements over v2:
1. Absolute Scoring (Winsorized Min-Max) instead of Rank-Percentile to fix IIA violation.
2. Volume Tier segmentation to differentiate performance on high vs low volume items.
3. Configurable weights and bounds via ScorerConfig.
4. Multi-metric Win Reasoning (explaining WHY a model won).
5. Baseline Tie-Breaker (reverting to a known baseline if the challenger isn't significantly better).
6. Composite Recommendation Confidence based on p-values, effect size, and win rates.

Usage:
    python model_scorer.py <path_to_excel.xlsx> [--min-rows 30] [--out report.xlsx]
"""

import argparse
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from dataclasses import dataclass, field
import warnings

# Suppress scipy warnings if wilcoxon sample size is small
warnings.filterwarnings("ignore")

@dataclass
class ScorerConfig:
    weights: dict = field(default_factory=lambda: {"WAPE": 0.35, "Hit10": 0.25, "Bias": 0.20, "Stability": 0.20})
    hit_band: float = 0.10
    min_rows: int = 30
    baseline_model: str = "Manual"
    # Normalization bounds for Winsorized Min-Max
    wape_bounds: tuple = (0.05, 0.40)   # 5% is perfect 1.0, 40% is 0.0
    bias_bounds: tuple = (0.00, 0.20)   # 0% is perfect 1.0, 20% is 0.0
    stab_bounds: tuple = (0.00, 0.30)   # 0% is perfect 1.0, 30% IQR is 0.0
    hit10_bounds: tuple = (0.90, 0.30)  # 90% is perfect 1.0, 30% is 0.0
    min_wape_improvement: float = 0.015 # 1.5% absolute WAPE improvement required for high confidence
    sig_alpha: float = 0.05


def load_backtest(path: str) -> pd.DataFrame:
    """Load the forecast file and restrict to rows with a realized actual."""
    df = pd.read_excel(path)
    required = {"ML_Forecast", "Actual_Offered", "Model", "Family", "Week_Ending"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    bt = df[df["Actual_Offered"].notna()].copy()
    if bt.empty:
        raise ValueError("No backtested rows found (Actual_Offered is empty everywhere).")

    bt["err"] = bt["ML_Forecast"] - bt["Actual_Offered"]
    bt["abs_err"] = bt["err"].abs()
    with np.errstate(divide="ignore", invalid="ignore"):
        bt["pct_err"] = bt["err"] / bt["Actual_Offered"]
        
    return bt


def add_volume_tiers(bt: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    """
    Assigns volume tiers (High/Medium/Low) based on the mean volume per segment.
    """
    vols = bt.groupby(segment_col)["Actual_Offered"].mean()
    if vols.nunique() < 3:
        tiers = pd.Series("Medium", index=vols.index)
    else:
        tiers = pd.qcut(vols, q=3, labels=["Low", "Medium", "High"], duplicates='drop')
    
    bt = bt.merge(tiers.rename("Volume_Tier"), on=segment_col, how="left")
    return bt


def _raw_metrics(g: pd.DataFrame, hit_band: float) -> pd.Series:
    """Compute the four raw metrics + sample-size stats for one group."""
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
        "StdErrPct": pct_err_clean.std(),      # diagnostic only, not scored
        "IQR_Stability": q75 - q25,             # robust spread -- this is scored
        "Hit10": (pct_err_clean.abs() <= hit_band).mean(),
    })


def _normalize_absolute(s: pd.Series, best: float, worst: float) -> pd.Series:
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


def compute_confidence(series_a: pd.Series, series_b: pd.Series, alpha: float, effect_size: float, min_effect: float) -> tuple[str, float, float]:
    """
    Computes statistical and business confidence between two weekly WAPE series.
    Returns (Confidence_Level, p_value, win_rate).
    """
    common = series_a.index.intersection(series_b.index)
    if len(common) < 5:
        return "Low", np.nan, np.nan
    
    # Positive if A is better (lower WAPE)
    diff = series_b[common] - series_a[common]
    win_rate = (diff > 0).mean()
    
    try:
        stat, p = wilcoxon(series_a[common], series_b[common])
    except ValueError:
        p = np.nan
        
    if pd.isna(p):
        return "Low", np.nan, win_rate
        
    # High confidence: Statistically significant AND consistent wins AND sufficient effect size
    if p < alpha and win_rate >= 0.6 and effect_size >= min_effect:
        return "High", p, win_rate
    # Medium confidence: (Marginally significant OR highly consistent) AND sufficient effect size
    elif (p < 0.15 or win_rate >= 0.7) and effect_size >= (min_effect / 2):
        return "Medium", p, win_rate
    else:
        return "Low", p, win_rate


def generate_win_reasoning(row_winner: pd.Series, row_runner_up: pd.Series, tied: bool, conf: str, opponent_name: str) -> str:
    """Deterministically explains why a model was recommended."""
    if tied:
        return f"Performance is too similar to {opponent_name} to justify replacing the baseline."
    
    adv = []
    # Relative checks
    w_wape, r_wape = row_winner["WAPE"], row_runner_up["WAPE"]
    w_stab, r_stab = row_winner["IQR_Stability"], row_runner_up["IQR_Stability"]
    w_bias, r_bias = row_winner["AbsBias"], row_runner_up["AbsBias"]
    
    if conf == "High":
        if w_wape < r_wape * 0.95:
            adv.append(f"superior accuracy (WAPE {w_wape:.1%} vs {opponent_name} {r_wape:.1%})")
        elif w_wape < r_wape:
            adv.append("better accuracy")
            
        if w_stab < r_stab * 0.85:
            adv.append("significantly lower volatility")
            
        if w_bias < r_bias * 0.80:
            adv.append("lower bias")
    else:
        if w_wape < r_wape:
            adv.append(f"marginally better accuracy (WAPE {w_wape:.1%} vs {opponent_name} {r_wape:.1%})")
        if w_stab < r_stab:
            adv.append("slightly lower volatility")
        if w_bias < r_bias:
            adv.append("marginally lower bias")
            
    if not adv:
        return f"a slightly better overall composite score than {opponent_name}"
        
    return f"{' and '.join(adv)}"


def score_group(bt: pd.DataFrame, group_col: str, config: ScorerConfig) -> pd.DataFrame:
    """Compute raw metrics + composite score for every value of group_col."""
    # Ensure min rows check handles nan/empty
    raw = bt.groupby(group_col).apply(lambda g: _raw_metrics(g, config.hit_band))
    if raw.empty:
        return pd.DataFrame()

    scored = raw[raw["n_rows"] >= config.min_rows].copy()
    excluded = raw[raw["n_rows"] < config.min_rows].copy()

    if not scored.empty:
        s_wape = _normalize_absolute(scored["WAPE"], *config.wape_bounds)
        s_bias = _normalize_absolute(scored["AbsBias"], *config.bias_bounds)
        s_stab = _normalize_absolute(scored["IQR_Stability"], *config.stab_bounds)
        s_hit10 = _normalize_absolute(scored["Hit10"], *config.hit10_bounds)
        
        scored["CompositeScore"] = (
            config.weights["WAPE"] * s_wape
            + config.weights["Hit10"] * s_hit10
            + config.weights["Bias"] * s_bias
            + config.weights["Stability"] * s_stab
        ) * 100
        scored = scored.sort_values("CompositeScore", ascending=False)

    excluded["CompositeScore"] = np.nan
    excluded["status"] = f"insufficient data (<{config.min_rows} rows)"
    if not scored.empty:
        scored["status"] = "scored"

    out = pd.concat([scored, excluded]).round(4)
    out.index.name = group_col
    return out.reset_index()


def generate_recommendations(bt: pd.DataFrame, group_col: str, scored: pd.DataFrame, config: ScorerConfig) -> pd.DataFrame:
    """
    Takes the leaderboard and determines the actual recommended model with evidence and confidence.
    """
    if scored.empty:
        return scored

    ranked = scored[scored["status"] == "scored"].sort_values("CompositeScore", ascending=False)
    
    results = scored.copy()
    results["Is_Top_Scorer"] = False
    results["Recommended"] = False
    results["Recommendation_Reason"] = ""
    results["Confidence"] = "Low"
    results["p_value"] = np.nan
    results["Win_Rate_vs_Challenger"] = np.nan
    
    if ranked.empty:
        return results
        
    if len(ranked) == 1:
        idx = ranked.index[0]
        results.at[idx, "Is_Top_Scorer"] = True
        results.at[idx, "Recommended"] = True
        results.at[idx, "Recommendation_Reason"] = "Only model with sufficient data."
        return results
        
    def weekly_wape(name):
        sub = bt[bt[group_col] == name]
        return sub.groupby("Week_Ending").apply(
            lambda g: g["abs_err"].sum() / g["Actual_Offered"].sum() if g["Actual_Offered"].sum() else np.nan
        )
        
    leader = ranked.iloc[0]
    leader_name = leader[group_col]
    results.at[leader.name, "Is_Top_Scorer"] = True
    
    # Identify the baseline model row (if present and scored)
    baseline_in_ranked = config.baseline_model in ranked[group_col].values
    baseline_row = ranked[ranked[group_col] == config.baseline_model].iloc[0] if baseline_in_ranked else None
    
    # If the leader is the baseline, it wins trivially
    if leader_name == config.baseline_model:
        recommended_row = leader
        challenger_row = ranked.iloc[1]
        tied_due_to_margin = False
    else:
        # Leader is a challenger. We must compare it to the baseline (if it exists) or the runner-up.
        challenger_row = baseline_row if baseline_row is not None else ranked.iloc[1]
        
        effect_size = challenger_row["WAPE"] - leader["WAPE"]
        weekly_rec = weekly_wape(leader_name)
        weekly_chal = weekly_wape(challenger_row[group_col])
        conf, p, win_rate = compute_confidence(weekly_rec, weekly_chal, config.sig_alpha, effect_size, config.min_wape_improvement)
        
        # Operational Recommendation Logic:
        # A challenger only replaces the baseline if Confidence is Medium or High.
        if baseline_row is not None and conf == "Low":
            recommended_row = baseline_row
            challenger_row = leader  # the leader was rejected
            tied_due_to_margin = True
        else:
            recommended_row = leader
            tied_due_to_margin = False

    # Recalculate confidence for the final chosen matchup if we flipped to baseline or leader is baseline
    if recommended_row[group_col] != leader_name or leader_name == config.baseline_model:
        effect_size = challenger_row["WAPE"] - recommended_row["WAPE"]
        weekly_rec = weekly_wape(recommended_row[group_col])
        weekly_chal = weekly_wape(challenger_row[group_col])
        conf, p, win_rate = compute_confidence(weekly_rec, weekly_chal, config.sig_alpha, effect_size, config.min_wape_improvement)

    opponent_name = challenger_row[group_col]
    reason = generate_win_reasoning(recommended_row, challenger_row, tied=tied_due_to_margin, conf=conf, opponent_name=opponent_name)
    
    if not tied_due_to_margin:
        reason = f"Recommended over {opponent_name} due to " + reason + "."
    
    idx = recommended_row.name
    results.at[idx, "Recommended"] = True
    results.at[idx, "Recommendation_Reason"] = reason
    results.at[idx, "Confidence"] = conf
    results.at[idx, "p_value"] = p
    results.at[idx, "Win_Rate_vs_Challenger"] = win_rate
        
    # Keep original status='scored' logic and format nicely
    return results.sort_values(["status", "Recommended", "CompositeScore"], ascending=[True, False, False])


def score_by_segment(bt: pd.DataFrame, group_col: str, segment_col: str, config: ScorerConfig) -> pd.DataFrame:
    """
    Re-run the composite scoring independently within each value of segment_col.
    """
    results = []
    for seg_val, seg_df in bt.groupby(segment_col):
        scored = score_group(seg_df, group_col, config)
        recs = generate_recommendations(seg_df, group_col, scored, config)
        recs.insert(0, segment_col, seg_val)
        results.append(recs)
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


def top_per_segment(segment_scores: pd.DataFrame, segment_col: str, group_col: str) -> pd.DataFrame:
    """Pull out just the Recommended model per segment."""
    if segment_scores.empty:
        return pd.DataFrame()
    scored_only = segment_scores[segment_scores["status"] == "scored"]
    recommended = scored_only[scored_only["Recommended"] == True]
    return recommended.sort_values(segment_col).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Decision Intelligence Engine for Model Selection")
    parser.add_argument("excel_path", help="Path to the forecast Excel file")
    parser.add_argument("--min-rows", type=int, default=30, help="Minimum backtested rows")
    parser.add_argument("--out", default="model_scorecard.xlsx", help="Output workbook path")
    args = parser.parse_args()

    config = ScorerConfig(min_rows=args.min_rows)
    bt = load_backtest(args.excel_path)
    
    # Add Volume Tiers based on Family
    if "Family" in bt.columns:
        bt = add_volume_tiers(bt, "Family")
    else:
        bt["Volume_Tier"] = "Unknown"
    
    # Calculate coverage
    total_weeks = pd.read_excel(args.excel_path)["Week_Ending"].nunique()
    backtested_weeks = bt["Week_Ending"].nunique()
    print(f"Backtest coverage: {backtested_weeks}/{total_weeks} weeks have realized actuals.")

    # 1. Overall Scoring & Recommendations
    family_scored = score_group(bt, "Family", config)
    family_recs = generate_recommendations(bt, "Family", family_scored, config)
    
    model_scored = score_group(bt, "Model", config)
    model_recs = generate_recommendations(bt, "Model", model_scored, config)

    # 2. Segment Scoring & Recommendations
    family_by_region = score_by_segment(bt, "Family", "Region", config)
    family_by_channel = score_by_segment(bt, "Family", "Channel", config)
    family_by_volume = score_by_segment(bt, "Family", "Volume_Tier", config)

    # 3. Winners by Segment
    family_winner_by_region = top_per_segment(family_by_region, "Region", "Family")
    family_winner_by_channel = top_per_segment(family_by_channel, "Channel", "Family")
    family_winner_by_volume = top_per_segment(family_by_volume, "Volume_Tier", "Family")

    with pd.ExcelWriter(args.out, engine="openpyxl") as writer:
        pd.DataFrame({
            "metric": ["Total weeks in file", "Backtested weeks (have actuals)", "Coverage %"],
            "value": [total_weeks, backtested_weeks, round(100 * backtested_weeks / total_weeks, 1)],
        }).to_excel(writer, sheet_name="README", index=False)
        
        family_recs.to_excel(writer, sheet_name="Family_Overall", index=False)
        model_recs.to_excel(writer, sheet_name="Model_Overall", index=False)
        family_by_region.to_excel(writer, sheet_name="Family_by_Region", index=False)
        family_by_channel.to_excel(writer, sheet_name="Family_by_Channel", index=False)
        family_by_volume.to_excel(writer, sheet_name="Family_by_Volume", index=False)
        family_winner_by_region.to_excel(writer, sheet_name="Winner_by_Region", index=False)
        family_winner_by_channel.to_excel(writer, sheet_name="Winner_by_Channel", index=False)
        family_winner_by_volume.to_excel(writer, sheet_name="Winner_by_Volume", index=False)

    print(f"Wrote scorecard to {args.out}")
    
    print("\n--- RECOMMENDED FAMILY ---")
    rec_family = family_recs[family_recs["Recommended"] == True]
    if not rec_family.empty:
        for k, v in rec_family.iloc[0].to_dict().items():
            print(f"{k}: {v}")
    
    print("\n--- RECOMMENDED MODEL ---")
    rec_model = model_recs[model_recs["Recommended"] == True]
    if not rec_model.empty:
        for k, v in rec_model.iloc[0].to_dict().items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()