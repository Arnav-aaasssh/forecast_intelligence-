# analytics_spec.md

# Forecast Review & Decision Support System

## Analytics Engine Specification

---

# 1. Purpose

This document defines the analytical logic implemented by the Forecast Review Engine.

It specifies:

* Business metrics
* Mathematical formulas
* Decision rules
* Thresholds
* Module responsibilities
* Dependencies between analytics modules

The purpose is to ensure that all analytics are deterministic, consistent, explainable, and independent of the LLM.

---

# 2. Design Philosophy

## Python = Truth

All calculations are performed by deterministic Python modules.

These include:

* Accuracy
* Forecast Error
* Forecast Drift
* Historical Variance
* Risk Score
* Rankings

The outputs are considered authoritative.

---

## LLM = Narrative

The LLM never performs calculations.

It receives structured analytical outputs and converts them into:

* Executive summaries
* Business narratives
* Recommendations
* Answers to user questions

---

# 3. Analytics Pipeline

Forecast Dataset

↓

Validation Layer

↓

Performance Analysis

↓

Forecast Comparison

↓

Forecast Drift

↓

Historical Analysis

↓

Holiday Analysis

↓

Forecaster Analysis

↓

Risk Intelligence

↓

Insight Generation

↓

Recommendation Engine

↓

LLM Narrative Generation

↓

Forecast Review Package

---

# 4. Module Specifications

## Module 1 – Performance Analysis

### Purpose

Measure forecast quality by comparing forecast values with actual outcomes.

### Inputs

* Manual_Forecast
* ML_Forecast
* Actual_Offered

### Outputs

* Manual Accuracy
* ML Accuracy
* Manual Error
* ML Error
* Forecast Health Score

### Formula

Forecast Error

Error = Forecast − Actual

Forecast Accuracy

Accuracy = 1 − |Forecast − Actual| / Actual

### Business Rules

* Accuracy is capped between 0% and 100%.
* Division by zero returns a missing value.
* Manual and ML forecasts are evaluated independently.

---

## Module 2 – Forecast Comparison

### Purpose

Determine which forecasting approach performs better.

### Inputs

* Manual Accuracy
* ML Accuracy
* Manual_Adh
* ML_Adh

### Outputs

* Winning Method
* Win Rate
* Accuracy Difference
* Improvement %

### Decision Logic

If ML Accuracy > Manual Accuracy

Winner = ML

Else

Winner = Manual

---

## Module 3 – Forecast Drift

### Purpose

Measure how forecasts have changed since the previous planning cycle.

### Inputs

* Previous_Forecast
* Manual_Forecast
* ML_Forecast

### Formula

Forecast Drift

(Current Forecast − Previous Forecast)

/

Previous Forecast

### Outputs

* Drift %
* Drift Direction
* Drift Severity

### Thresholds

| Drift  | Category |
| ------ | -------- |
| 0–5%   | Stable   |
| 5–10%  | Moderate |
| 10–15% | Elevated |
| >15%   | High     |

---

## Module 4 – Historical Analysis

### Purpose

Compare current forecasts against historical behaviour.

### Inputs

* Final_Y1
* Final_Y2
* Final_Y3
* Final_Y4
* Final_Y5
* Historical Mean
* Historical Std Dev

### Outputs

* Historical Variance
* Trend Direction
* Coefficient of Variation

### Formula

Coefficient of Variation

Std Dev / Historical Mean

---

## Module 5 – Holiday Analysis

### Purpose

Evaluate the effect of holidays on forecast stability.

### Inputs

* Holiday_Count
* Monday–Sunday

### Outputs

* Holiday Impact Score
* Seasonality Indicator

### Business Rule

Higher holiday counts increase forecast uncertainty.

---

## Module 6 – Forecaster Analysis

### Purpose

Evaluate forecast consistency by planner.

### Inputs

* Forecaster
* Manual_Adh
* ML_Adh

### Outputs

* Average Accuracy
* Consistency Score
* Ranking

---

## Module 7 – Risk Intelligence

### Purpose

Generate a consolidated risk assessment.

### Inputs

Outputs from:

* Performance
* Drift
* Historical
* Holiday

Plus:

* Existing Risk Category
* Existing Risk Flag

### Formula

Risk Score

40%

Accuracy Risk

*

20%

Drift Risk

*

20%

Historical Volatility

*

20%

Holiday Impact

### Outputs

* Risk Score
* Risk Level
* Risk Drivers
* Priority

### Risk Thresholds

| Score | Level    |
| ----- | -------- |
| 0–25  | Low      |
| 25–50 | Medium   |
| 50–75 | High     |
| >75   | Critical |

---

## Module 8 – Insight Generation

### Purpose

Convert analytics into business findings.

No AI is used.

### Example

Input

Accuracy = 61%

Drift = 18%

Risk = High

Output

"Forecast accuracy has declined significantly while forecast revisions have increased."

---

## Module 9 – Recommendation Engine

### Purpose

Generate deterministic recommendations.

### Example Rules

IF

Risk = Critical

THEN

Recommend immediate review.

IF

Accuracy < 70%

THEN

Review forecasting assumptions.

IF

Holiday Impact = High

THEN

Validate seasonal demand adjustments.

---

## Module 10 – Model Selection (Decision Intelligence Engine)

### Purpose

Produce a deterministic, absolute recommendation for the best forecasting model/family, solving the Independence of Irrelevant Alternatives (IIA) violation.

### Inputs

* `WAPE`
* `AbsBias`
* `IQR_Stability`
* `Hit10`

### Outputs

* Absolute Composite Score (0-100)
* Recommended Model (Boolean)
* Recommendation Reason (Multi-metric reasoning)
* Confidence Level (High/Medium/Low)
* p_value (Wilcoxon signed-rank)

### Formula

Winsorized Min-Max Normalization:
`Score = (Worst_Bound - Clipped_Metric) / (Worst_Bound - Best_Bound)`

Composite Score Calculation:
`Composite Score = (0.35 * s_wape) + (0.25 * s_hit10) + (0.20 * s_bias) + (0.20 * s_stab)`

### Business Rules

* If data points < 30, the model is excluded from scoring.
* Models within `3.0` points of each other are considered tied.
* If tied, the system reverts to the `Manual` baseline model (if present).
* Statistical significance requires both `p_value < 0.05` and `Win Rate > 60%` for High Confidence.

---

# 5. Dependencies

Performance

↓

Comparison

↓

Drift

↓

History

↓

Holiday

↓

Forecaster

↓

Risk

↓

Insights

↓

Recommendations

↓

Model Selection (Decision Intelligence)

Every module depends only on documented outputs from previous modules.

---

# 6. Output Contract

Each analytics module returns:

* Summary metrics
* Row-level metrics (where applicable)
* Warnings
* Metadata

No module generates presentation-ready content.

---

# 7. LLM Contract

The LLM receives only structured analytics.

Example Input

{
"manual_accuracy": 72.4,
"ml_accuracy": 88.1,
"risk_level": "High",
"top_driver": "Forecast Drift"
}

Example Output

```json
{
  "executive_summary": "ML forecasts continue to outperform manual forecasts, though overall reliability has dropped.",
  "risk_explanation": "Elevated forecast drift has increased operational risk, specifically driven by late-cycle revisions.",
  "comparison_summary": "The ML method remains superior with an 88.1% accuracy compared to the manual 72.4%.",
  "recommendation_narrative": "Immediate management review is recommended for the drift drivers."
}
```

The LLM must never:

* Compute KPIs
* Calculate scores
* Modify analytical results
* Override business rules

---

# 8. Guiding Principles

1. Every metric must be reproducible.
2. Every insight must be explainable.
3. Every recommendation must be traceable to a business rule.
4. Analytics precede AI.
5. Python is the source of truth.
6. The LLM is responsible only for communication.
