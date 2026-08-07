# Current Engine Policy Specification

## PART 1 — COMPOSITE SCORING POLICY
The engine calculates a composite score by normalizing absolute performance bounds for each metric and applying a weighted sum.

*   **Composite Score Formula:** `(WAPE_weight * s_wape + Hit10_weight * s_hit10 + Bias_weight * s_bias + Stability_weight * s_stab) * 100`
*   **WAPE Weight:** 0.35 (35%)
*   **Hit10 Weight:** 0.25 (25%)
*   **Bias Weight:** 0.20 (20%)
*   **Stability (IQR) Weight:** 0.20 (20%)
*   **Additional Metrics Included:** None.
*   **Composite Score Normalization Formula:** `normalize_absolute(s, best, worst)` uses Winsorized Min-Max.
*   **Clipping/Scaling Logic:** Values are clipped to `[best, worst]` (or `[worst, best]`), then scaled to a `[0, 1]` range:
    *   If best < worst: `(worst - clipped) / (worst - best)`
    *   If best >= worst: `(clipped - worst) / (best - worst)`

**Parameter Traceability:**
*   **Weights:** Current Value `{"WAPE": 0.35, "Hit10": 0.25, "Bias": 0.20, "Stability": 0.20}` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 6
*   **Normalization Logic:** Current Value `Min-Max Scaling` | File: `analytics/stats_utils.py` | Function: `normalize_absolute` | Line: 6-16
*   **Composite Formula:** Current Value `Weighted Sum * 100` | File: `analytics/performance.py` | Function: `score_group` | Line: 47-52

## PART 2 — NORMALIZATION POLICY
Bounds for metrics represent "best" and "worst" allowable thresholds for normalization. Values outside these bounds are winsorized (clipped).

*   **Winsorization Bounds:**
    *   **WAPE Bounds:** `(0.05, 0.40)` (Best: 5%, Worst: 40%)
    *   **Bias Bounds:** `(0.00, 0.20)` (Best: 0%, Worst: 20%)
    *   **Stability Bounds:** `(0.00, 0.30)` (Best: 0%, Worst: 30%)
    *   **Hit10 Bounds:** `(0.90, 0.30)` (Best: 90%, Worst: 30%)
*   **Outlier Handling:** Outliers beyond the upper/lower limits are clipped to the nearest limit boundary before normalization.
*   **Missing Value Handling:** Missing actuals (`Actual_Offered = NaN`) are dropped entirely prior to analytics. Infinite percentage errors are replaced with `NaN` during metrics computation.

**Parameter Traceability:**
*   **WAPE Bounds:** Current Value `(0.05, 0.40)` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 7
*   **Bias Bounds:** Current Value `(0.00, 0.20)` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 8
*   **Stability Bounds:** Current Value `(0.00, 0.30)` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 9
*   **Hit10 Bounds:** Current Value `(0.90, 0.30)` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 10
*   **Missing Actual Handling:** Current Value `Dropna` | File: `decision_orchestrator.py` | Function: `load_backtest` | Line: 38
*   **Infinite Error Handling:** Current Value `Replace with NaN` | File: `analytics/performance.py` | Function: `raw_metrics` | Line: 9

## PART 3 — AGGREGATION POLICY
Metrics are computed at the group level (Model, Region, Channel). Aggregations are **row pooled** within each group. They are NOT segment averaged or equal weighted.

*   **WAPE Aggregation:** Volume weighted (row pooled sum of absolute errors divided by row pooled sum of actuals). Implementation: `g["abs_err"].sum() / denom`
*   **Bias Aggregation:** Volume weighted (row pooled sum of errors divided by row pooled sum of actuals). Implementation: `g["err"].sum() / denom`
*   **Stability (IQR) Aggregation:** Equal weighted calculation of the Interquartile Range (75th percentile - 25th percentile) on percentage error for the pooled rows. Implementation: `q75 - q25`
*   **Hit10 Aggregation:** Equal weighted mean of rows where absolute percentage error is ≤ `hit_band` (0.10). Implementation: `(pct_err_clean.abs() <= hit_band).mean()`

**Parameter Traceability:**
*   **WAPE Formula:** Current Value `Sum(AbsErr)/Sum(Actual)` | File: `analytics/performance.py` | Function: `raw_metrics` | Line: 11
*   **Bias Formula:** Current Value `Sum(Err)/Sum(Actual)` | File: `analytics/performance.py` | Function: `raw_metrics` | Line: 12
*   **Hit10 Band:** Current Value `0.10` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 11
*   **IQR Formula:** Current Value `P75 - P25` | File: `analytics/performance.py` | Function: `raw_metrics` | Line: 13, 21

## PART 4 — MODEL ELIGIBILITY POLICY
Models must satisfy minimum requirements to be scored and considered for recommendation.

*   **Minimum Rows:** 30. Models with `< 30` rows have their status set to `"insufficient data (<30 rows)"` and are excluded from normalization and composite scoring.
*   **Minimum Weeks:** Computed but NOT enforced as an eligibility rule.
*   **Minimum Observations:** Only row count is enforced.
*   **Missing Actual Handling:** Rows with null `Actual_Offered` are dropped across the entire dataset.
*   **Null Handling:** Nulls in `pct_err` are ignored during quantile and mean functions inherently via Pandas implementation.

**Parameter Traceability:**
*   **Min Rows:** Current Value `30` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 12
*   **Row Exclusion Logic:** Current Value `Filter < 30` | File: `analytics/performance.py` | Function: `score_group` | Line: 37

## PART 5 — GLOBAL CHAMPION POLICY
The engine determines the champion based purely on the `CompositeScore` among models that met the eligibility policy (status = `scored`). 

*   **Minimum Segment Coverage:** Not enforced. A model with 30 rows in one channel competes directly against a model with 10,000 rows globally.
*   **Coverage Calculation Method:** Uses Pandas `groupby(group_col)` which counts all rows attributed to a given model name.
*   **Grouping:** `Model` column acts as the grouping key for ranking. Region and Channel level champions are generated independently by looping over `Region` and `Channel` columns if available.

**Parameter Traceability:**
*   **Champion Selection:** Current Value `Sort by CompositeScore` | File: `analytics/recommendation.py` | Function: `generate_recommendations` | Line: 21

## PART 6 — CONFIDENCE POLICY
Confidence is statistically derived from pairwise comparisons of weekly WAPE between the recommended model and the challenger/baseline.

*   **High Confidence:** `p_value < 0.05` AND `win_rate >= 0.6` AND `effect_size >= 0.015`
*   **Medium Confidence:** (`p_value < 0.15` OR `win_rate >= 0.7`) AND `effect_size >= 0.0075` (min_wape_improvement / 2)
*   **Low Confidence:** Fallback case if above conditions fail, OR if the intersection of weeks between models is `< 5`.

**Parameter Traceability:**
*   **Alpha Threshold (High):** Current Value `0.05` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 14
*   **Alpha Threshold (Medium):** Current Value `0.15` (Hardcoded) | File: `analytics/stats_utils.py` | Function: `compute_confidence` | Line: 43
*   **Effect Size Threshold:** Current Value `0.015` | File: `analytics/models.py` | Class: `ScorerConfig` | Line: 13
*   **Small Sample Suppression:** Current Value `n < 5` | File: `analytics/stats_utils.py` | Function: `compute_confidence` | Line: 24

## PART 7 — DECISION POLICY
Business thresholds govern final deployment decisions (action output).

*   **Min Confidence to Switch:** "Medium" (If baseline exists, baseline is retained if stats_evidence confidence < "Medium").
*   **Regional Min Improvement:** 1.0% (0.010) WAPE absolute improvement required over Global.
*   **Segmented Min Improvement:** 2.0% (0.020) WAPE absolute improvement required over Regional.
*   **Max Models Complexity:** Low = 1 model, Medium = ≤ 4 models, High = > 4 models.
*   **High Impact:** `abs_improvement >= 3.0%` OR `rel_improvement >= 20%`.
*   **Medium Impact:** `abs_improvement >= 1.0%` OR `rel_improvement >= 5%`.
*   **Greenfield Handling:** Defaults to `impact_rating = "High"`. Recommends "Full Global Switch" / "Segmented Switch" if confidence is Medium/High. Recommends "Pilot Deployment" if confidence is Low.
*   **Manual Baseline Handling:** Retains incumbent if impact is "Low" or confidence is "Low". Recommends Pilot if impact is "Medium".

**Parameter Traceability:**
*   **Min Switch Confidence:** Current Value `"Medium"` | File: `analytics/policy.py` | Class: `DecisionPolicy` | Line: 10
*   **Regional Improv Threshold:** Current Value `0.010` | File: `analytics/policy.py` | Class: `DecisionPolicy` | Line: 13
*   **Segmented Improv Threshold:** Current Value `0.020` | File: `analytics/policy.py` | Class: `DecisionPolicy` | Line: 14
*   **Complexity Limits:** Current Value `Low=1, Med=4` | File: `analytics/policy.py` | Class: `DecisionPolicy` | Line: 18-19
*   **Impact Thresholds (High):** Current Value `Abs: 0.03, Rel: 0.20` | File: `analytics/policy.py` | Class: `DecisionPolicy` | Line: 22-23
*   **Impact Thresholds (Med):** Current Value `Abs: 0.01, Rel: 0.05` | File: `analytics/policy.py` | Class: `DecisionPolicy` | Line: 24-25
*   **Decision Matrix Logic:** Current Value `If/Else cascade` | File: `analytics/business_logic.py` | Function: `make_executive_decision` | Line: 132-152

## PART 8 — STATISTICAL POLICY
*   **Test:** Scipy Wilcoxon Signed-Rank Test (`scipy.stats.wilcoxon`).
*   **Alternative Hypothesis:** Two-sided (implicitly default since `alternative` parameter is not overridden).
*   **P-value threshold:** Checked dynamically against 0.05 (High) and 0.15 (Medium).
*   **Effect Size Calculation:** Absolute WAPE difference (`challenger_wape - leader_wape`).
*   **Tie Handling:** Uses scipy defaults (discard differences of zero).
*   **Small Sample Suppression:** Suppressed (Low Confidence, `np.nan` p-value) if common overlapping weeks < 5.
*   **Assumptions:** Assumes weekly level comparisons are appropriate for statistical testing.

**Parameter Traceability:**
*   **Test Method:** Current Value `scipy.stats.wilcoxon` | File: `analytics/stats_utils.py` | Function: `compute_confidence` | Line: 32
*   **Effect Size Usage:** Current Value `challenger.wape - leader.wape` | File: `analytics/recommendation.py` | Function: `generate_recommendations` | Line: 55, 73

## PART 9 — REPORT POLICY
*   **Observations:** Content Layer deterministically constructs strings from numbers (e.g. `content/q3_builder.py` produces `"Demand variability was high (CV X%)"`).
*   **Conclusions:** Content Layer generates a single sentence based purely on configured logic flags.
*   **Recommendations:** Originate from the Decision Intelligence Layer (`make_executive_decision`), passed through as `action_recommendation`. The Content Layer optionally suppresses rendering but does not modify the recommendation text itself.
*   **Content Layer Computations:** Strictly prohibited from statistical computation. However, Q1 conditionally checks `delta >= 0.015` directly in the builder, and Q3 checks `cv > 0.15` in the builder.
*   **Decision Layer String Generation:** The Decision Layer (`business_logic.py`) generates narrative explanations in the `reasoning` field of `ExecutiveDecision`.
*   **Presentation Layer Logic:** Presentation layer (`report_generator.py`) performs ZERO logic other than looping over components and hiding suppressed recommendations.

## PART 10 — TRACEABILITY SUMMARY

| Parameter | Current Value | Source File | Function / Class | Line Number | Short Explanation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| WAPE Weight | 0.35 | `analytics/models.py` | `ScorerConfig` | 6 | Factor for CompositeScore |
| Hit10 Weight | 0.25 | `analytics/models.py` | `ScorerConfig` | 6 | Factor for CompositeScore |
| Bias Weight | 0.20 | `analytics/models.py` | `ScorerConfig` | 6 | Factor for CompositeScore |
| Stability Weight | 0.20 | `analytics/models.py` | `ScorerConfig` | 6 | Factor for CompositeScore |
| WAPE Bounds | `(0.05, 0.40)` | `analytics/models.py` | `ScorerConfig` | 7 | Normalization min/max |
| Bias Bounds | `(0.00, 0.20)` | `analytics/models.py` | `ScorerConfig` | 8 | Normalization min/max |
| Hit10 Bounds | `(0.90, 0.30)` | `analytics/models.py` | `ScorerConfig` | 10 | Normalization min/max |
| Stability Bounds | `(0.00, 0.30)` | `analytics/models.py` | `ScorerConfig` | 9 | Normalization min/max |
| Hit Band | 0.10 | `analytics/models.py` | `ScorerConfig` | 11 | +/- tolerance for Hit10 |
| Min Rows for Scoring | 30 | `analytics/models.py` | `ScorerConfig` | 12 | Row threshold for eligibility |
| Sig Alpha (High Conf) | 0.05 | `analytics/models.py` | `ScorerConfig` | 14 | P-value threshold |
| Sig Alpha (Med Conf) | 0.15 | `analytics/stats_utils.py` | `compute_confidence` | 43 | Hardcoded p-value threshold |
| Small Sample Suppression | 5 | `analytics/stats_utils.py` | `compute_confidence` | 24 | Min weeks for Wilcoxon |
| Min Confidence to Switch | "Medium" | `analytics/policy.py` | `DecisionPolicy` | 10 | Migration condition |
| Regional Abs Improv | 0.010 | `analytics/policy.py` | `DecisionPolicy` | 13 | Global -> Reg threshold |
| Segmented Abs Improv | 0.020 | `analytics/policy.py` | `DecisionPolicy` | 14 | Reg -> Seg threshold |
| Max Low Complexity | 1 | `analytics/policy.py` | `DecisionPolicy` | 18 | Model count bound |
| Max Med Complexity | 4 | `analytics/policy.py` | `DecisionPolicy` | 19 | Model count bound |
| Impact High Abs | 0.03 | `analytics/policy.py` | `DecisionPolicy` | 22 | ROI rating threshold |
| Impact Med Abs | 0.01 | `analytics/policy.py` | `DecisionPolicy` | 24 | ROI rating threshold |
| Anomaly Z-Score | 2.5 | `analytics/actuals.py` | `analyze_actuals` | 44 | Identifies high var weeks |
| Volatility CV High | 0.15 | `content/q3_builder.py` | `build_q3_actuals` | 55 | High volatility trigger |
| Meaningful Q1 Delta | 0.015 | `content/q1_builder.py` | `build_q1_assessment` | 36 | Hardcoded minimum change |
| Trend Norm Slope | 0.02 | `analytics/actuals.py` | `analyze_actuals` | 35 | Evaluates linear incline |

## PART 11 — CONSISTENCY AUDIT

*   **Undocumented / Hardcoded Policies:** 
    *   The `Medium` confidence p-value threshold (`p < 0.15`) is hardcoded in `stats_utils.py` (Line 43) instead of existing in `ScorerConfig`.
    *   Anomaly detection Z-Score bound `> 2.5` is hardcoded directly into `analytics/actuals.py` (Line 44).
    *   The high volatility definition `cv > 0.15` is hardcoded directly in the Content Engine layer (`content/q3_builder.py`, Line 55), meaning the presentation layer contains business logic.
    *   The Q1 improvement threshold `delta >= 0.015` is hardcoded in `content/q1_builder.py` (Line 36), causing the Content layer to duplicate the `ScorerConfig.min_wape_improvement` threshold.
    *   Trend significance bound `norm_slope > 0.02` is hardcoded directly into `analytics/actuals.py` (Line 35).
    *   Complexity `High` is dynamically inferred simply by exceeding `max_models_medium_complexity` rather than possessing an explicit maximum bound.
*   **Duplicate Policies:**
    *   `min_wape_improvement` is defined in `ScorerConfig` (0.015) for analytical usage but duplicated as hardcoded `0.015` inside `q1_builder.py`.
*   **Hidden Assumptions:**
    *   Model eligibility completely relies on `n_rows` regardless of data density/time-continuity. `n_weeks` is derived but is never asserted as an exclusion constraint prior to the Wilcoxon test.
    *   `scipy.stats.wilcoxon` relies on the default zero-difference treatment (`zero_method="wilcox"`) rather than explicitly specifying a handler for tied weeks.
    *   Volume is assumed to map flawlessly to `Week_Ending`, ignoring any non-uniform periods.
    *   Greenfield deployment business impact is hard-coded as `"High"` in `evaluate_business_impact` instead of using a configurable policy mapping.
