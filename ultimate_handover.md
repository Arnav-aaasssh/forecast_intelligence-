# Ultimate Handover Document
## Forecast Decision Intelligence Dashboard — Complete Strategic & Technical Reference

---

## 1. What Are We Trying to Achieve?

### The Business Problem
An enterprise runs a global contact-center operation spanning 3 Regions (APJ, Americas, EMEA), 14 Sub-Regions, 5 Channels (Voice, Chat, Email, Social Media, Case), 3 Offerings (Basic, Pro, Premium), and approximately 360 individual forecasting queues. Every week, two forecasts are produced for each queue:

1. **Manual Forecast** — created by human planners using institutional knowledge, seasonal intuition, and spreadsheet-based adjustments.
2. **ML Forecast** — created by machine learning models (92 model variants across 4 algorithm families: Prophet, ARIMA, Linear Regression, XGBoost).

The fundamental question this dashboard exists to answer:

> **Should the organization trust the Machine Learning forecasts enough to replace the Manual forecasts — and at which level of the organization is that trust justified?**

This is not a binary, global yes/no question. ML may be dramatically better in EMEA Voice but worse in APJ Chat. The head of APJ needs an answer for APJ. The head of EMEA needs an answer for EMEA. The global VP of Operations needs an answer for the entire business. Each answer must be backed by traceable, auditable evidence.

### The Dashboard's Role
The dashboard is a **decision-support instrument**, not a decision-making tool. It observes, measures, and presents. It never commands. Its job is to give each stakeholder — from the VP glancing for 10 seconds to the data scientist auditing for 15 minutes — exactly the evidence they need to make an informed decision about forecast methodology.

---

## 2. The Organizational Hierarchy

The data is structured as a tree. Every number on the dashboard is calculated by traversing this tree.

```
Global (1)
├── Region (3): APJ, Americas, EMEA
│   ├── SubRegion (14): ANZ, Brazil, CCC, CER, EC, IN, JPN, KR, LATAM, ...
│   │   ├── Channel (up to 5): Voice, Chat, Email, Social Media, Case
│   │   │   ├── Offering (up to 3): Basic, Pro, Premium
│   │   │   │   └── Forecast_Name (leaf): The individual queue
```

**Why this hierarchy matters:**
- The **Head of APJ** thinks in Regions and Sub-Regions. They want to know: "Is ML safe for my region?"
- The **Channel Manager** thinks in Channels. They want to know: "Is ML better for Voice specifically?"
- The **Offering Lead** thinks in Offerings. They want to know: "Does ML handle Premium queues well?"
- The **Global VP** thinks at the top. They want to know: "Across the board, is ML ready?"

The dashboard must serve all of these perspectives from the same dataset.

---

## 3. The Mathematical Framework

### 3.1 WAPE — The Primary Accuracy Metric

**Weighted Absolute Percentage Error** is the single metric used to evaluate forecast accuracy. It was chosen because:

- It is **volume-weighted by construction** — a 10% error on 10,000 contacts matters more than a 10% error on 10 contacts.
- It is **non-negative and bounded below by zero** — making it easy to interpret (lower is better, 0% is perfect).
- It is **industry standard** for contact-center workforce management.
- It is **robust to zero-volume segments** — unlike MAPE, it doesn't divide by individual actuals.

$$\text{WAPE} = \frac{\sum_{i=1}^{n} |F_i - A_i|}{\sum_{i=1}^{n} A_i} \times 100\%$$

Where $F_i$ is the forecast for queue $i$ and $A_i$ is the actual volume for queue $i$.

### 3.2 Why WAPE Is Non-Additive (And Why That Matters)

WAPE is **non-additive**: you cannot average the WAPEs of two children to get the parent's WAPE.

**Example:**
| Queue | Actual | ML Forecast | Abs Error | WAPE |
|---|---|---|---|---|
| Chat | 100 | 120 | 20 | 20.0% |
| Voice | 10,000 | 10,050 | 50 | 0.5% |

- **Average WAPE** = (20% + 0.5%) / 2 = **10.25%** — Wrong. Gives equal weight to Chat (100 contacts) and Voice (10,000 contacts).
- **True WAPE** = (20 + 50) / (100 + 10,000) = 70 / 10,100 = **0.69%** — Correct. Voice dominates because it carries the volume.

This is why the dashboard **never averages WAPEs**. It always aggregates by summing raw absolute errors and raw actuals, then dividing.

### 3.3 How WAPE Rolls Up the Tree

For any node $N$ in the hierarchy (a Region, a SubRegion, a Channel, etc.) in a given week $w$:

1. **Collect all leaf rows** that belong to node $N$ in week $w$.
2. **Sum the absolute errors:** $\text{AbsError}(N, w) = \sum_{i \in \text{leaves}(N)} |F_i - A_i|$
3. **Sum the actuals:** $\text{Actual}(N, w) = \sum_{i \in \text{leaves}(N)} A_i$
4. **Compute WAPE:** $\text{WAPE}(N, w) = \frac{\text{AbsError}(N, w)}{\text{Actual}(N, w)} \times 100$

This is done separately for ML and Manual forecasts.

### 3.4 Winner Determination

For each node $N$ in each week $w$:
- **ML wins** if $\text{ML\_WAPE}(N, w) \leq \text{Manual\_WAPE}(N, w)$
- **Manual wins** otherwise

The total "ML Wins" and "Manual Wins" counts for a node are simply the sum across the 13 realized weeks.

### 3.5 What We Are NOT Doing

| Approach | Status | Reason |
|---|---|---|
| Averaging child WAPEs | Rejected | Non-additive; gives equal weight to tiny and massive queues |
| Top-Down Net Error | Rejected | `ABS(SUM(F) - SUM(A))` allows over-forecasts to cancel under-forecasts, hiding misallocation errors |
| Majority vote of children | Rejected | A region with 20 tiny queues voting "ML" would outvote 1 massive queue voting "Manual" |
| Bottom-up WAPE aggregation (chosen) | Active | Volume-weighted by construction; additive at the numerator/denominator level; traceable |
| Causal claims ("ML lost because...") | Permanently banned | 13 weeks of backtest data, no external causal data. We observe WHAT happened, never claim WHY |

### 3.6 Supporting Statistical Tests

- **Wilcoxon Signed-Rank Test** — Non-parametric paired test on weekly absolute errors (ML vs Manual). Used to assess whether the difference between ML and Manual is statistically significant or could be due to chance.
  - **High Confidence:** p < 0.05
  - **Medium Confidence:** 0.05 <= p < 0.10
  - **Low Confidence:** p >= 0.10
  - **Inconclusive:** Fewer than 3 non-zero paired differences

- **Effect Size** — The raw difference in overall WAPE (ML WAPE minus Manual WAPE, in percentage points). Accompanies the p-value because a statistically significant but practically meaningless improvement (0.1pp) should not trigger deployment.

---

## 4. The Four Business Questions

The dashboard is structured around four permanent business questions. These are architectural decisions that will never change.

### Q1: Strategy Assessment — "Did ML or Manual Perform Better?"
- **What it shows:** Weekly WAPE time series for both ML and Manual, with a winner declared each week. Total ML Wins vs Manual Wins. Statistical confidence of the difference.
- **Why it matters:** This is the single most important question. If ML consistently wins with high confidence, it can be trusted. If Manual wins, ML needs more work.
- **Hierarchy Breakdown** — Shows the win/loss verdict at each child level of the current filter, so a regional head can see *which channels* are driving the overall result.

### Q2: Model Champion — "Which ML Model Ranked First?"
- **What it shows:** Composite score leaderboard of all 92 models, family-level comparison, score distribution.
- **Why it matters:** Even if ML wins overall, the *which* model matters for deployment. The champion model needs sufficient coverage, stability, and confidence.
- **Scoring weights:** WAPE (35%), Hit-within-10% (25%), Bias (20%), Stability (20%).

### Q3: Business Context — "Was Demand Stable Enough to Forecast Reliably?"
- **What it shows:** Realized vs planned volume trajectory, coefficient of variation, percentage of segments below historical baseline.
- **Why it matters:** If demand itself was volatile or structurally shifting, forecast accuracy may be poor regardless of methodology. Context prevents over-interpreting accuracy numbers during unusual periods.
- **This question never produces recommendations** — it provides context only.

### Q4: Anomaly Detection — "Did Accuracy Degrade During Demand Anomalies?"
- **What it shows:** Anomaly rate over time, WAPE comparison between normal and anomalous weeks, anomaly deep-dive cards.
- **Why it matters:** If ML degrades during anomalies but performs well during normal weeks, a hybrid strategy (ML for normal, Manual for anomalies) might be optimal.
- **This question never produces recommendations** — it provides context only.

---

## 5. The Dashboard's Philosophy

### 5.1 Evidence Over Recommendation
The dashboard shows what happened and measures how confident we are. It does **not** tell the user what to do. Recommendations are stated only when evidence and confidence are both sufficient. When either is lacking, the recommendation is **suppressed entirely** (not softened, not hedged — omitted).

### 5.2 Observation Over Causation
With 13 weeks of backtest data and no external causal variables (holidays, marketing campaigns, workforce changes), the system can only identify correlations and temporal patterns. Phrases like "ML lost because Voice volumes spiked" are permanently banned. The correct language is "ML accuracy was lower during weeks when Voice volumes were above the historical mean."

### 5.3 Page 1 Stands Alone
A VP reading only the Executive Overview tab must have sufficient information to confirm or challenge the current forecast methodology without scrolling or switching tabs.

### 5.4 Confidence Is a First-Class Visual Citizen
Confidence is never buried in text or hidden behind a tooltip. It is a colored chip (High/Medium/Low/Inconclusive) displayed prominently next to every claim. A Low-confidence finding must never be visually mistaken for a recommendation.

### 5.5 The Dashboard Serves the Hierarchy
The same underlying data serves three different attention budgets:
- **10 seconds** (VP): Decision + confidence, nothing else.
- **2 minutes** (Analyst): Which channels are driving the result? Any anomalies?
- **15 minutes** (Data Scientist): Full model leaderboard, scoring decomposition, policy audit.

---

## 6. The Data Architecture

### 6.1 Source Data
- **File:** `sample_data/Final_data.xlsx` — 35,640 rows x 45 columns
- **Grain:** Each row is one `(Week_Ending, Forecast_Name)` pair — one queue, one week
- **Key columns:**
  - `Actual_Offered` — realized contact volume (only 13 weeks have actuals)
  - `ML_Forecast` — machine learning forecast
  - `Manual_Forecast` — human planner forecast
  - `Region`, `SubRegion`, `Channel`, `Offering`, `Model`, `Family` — hierarchy dimensions

### 6.2 Processing Pipeline
1. **`app.py`** — CLI entry point, loads data, calls the service pipeline, then calls `generate_dashboard.py`
2. **`generate_dashboard.py`** — Takes the processed DataFrame, computes all chart data for all filter combinations, writes to `dashboard/data/report.json`
3. **`dashboard/index.html`** — Fetches `report.json`, renders the interactive dashboard

### 6.3 Report JSON Schema
```
report.json
├── metadata (title, period, models evaluated)
├── executive_recommendations (text-based guidance)
└── chart_data
    ├── filters (available filter values)
    └── global_slices
        ├── "All|All|All|All" → { q1: {...}, q2: {...}, q3: {...}, q4: {...} }
        ├── "ANZ|All|All|All" → { ... }
        ├── "ANZ|All|All|Voice" → { ... }
        └── ... (432+ pre-computed slices)
```

### 6.4 Excel Validation
- **File:** `Validation_Formulas_Master.xlsx`
- **Purpose:** Physical proof that the dashboard numbers are mathematically correct
- **Structure:**
  - `Raw_Data` tab — the source data with pre-computed absolute error columns
  - `Master_Weekly_Validation` tab — SUMIFS formulas that mirror the dashboard's calculations, filterable by `Dashboard_Slice`

---

## 7. What Is Changing (The Overhaul)

### Before (Current State)
- Dashboard computes WAPE by pooling all rows in a slice into one flat bucket
- No visibility into which children (Channels, Offerings) are driving the result
- No Region-level filter — only SubRegion
- No Offering-level filter
- Excel validation used inconsistent WAPE methodology, creating mismatches with the dashboard

### After (Target State)
- Dashboard computes WAPE at **every level of the hierarchy** within each slice
- Q1 includes a **hierarchy breakdown** showing per-child win/loss verdicts with volume weighting
- Region and Offering added as filter dimensions
- Cascading filters: selecting a Region auto-filters SubRegions
- Excel validation uses Bottom-Up WAPE (matching the dashboard exactly)
- Every number on the dashboard is physically verifiable in the Excel sheet

### What Is NOT Changing
- Q2 Model Scorecard — untouched (already operates at Model grain)
- Q3 Volume Intelligence — untouched (volume context, not accuracy)
- Q4 Anomaly Detection — untouched (anomaly behavior, not accuracy)
- The 4 business questions — permanent
- The design system (colors, typography, layout) — stable
- The prohibition on causal language — permanent
- The prohibition on financial hallucination — permanent
- The statistical testing framework (Wilcoxon) — permanent

---

## 8. How the Dashboard Answers Business Questions — By Persona

### Head of APJ
1. Opens dashboard, selects Region: APJ
2. Sees: **ML Wins: 7, Manual Wins: 6** (of 13 weeks) — close race
3. Sees: **Confidence: Low** — the difference is not statistically significant
4. Sees: **Hierarchy Breakdown:**
   - ANZ: ML wins 5, Manual wins 8 (Manual dominant — Email drives this)
   - IN: ML wins 10, Manual wins 3 (ML dominant — Voice and Chat)
   - CCC: ML wins 8, Manual wins 5 (ML edge)
5. **Conclusion:** "ML is better in India and CCC but worse in ANZ. I should not globally switch APJ to ML — I need a channel-by-channel strategy."

### Global VP of Operations
1. Opens dashboard, keeps all filters at "All" (Global view)
2. Sees: **ML Wins: 9, Manual Wins: 4** — ML leads
3. Sees: **Confidence: High** — statistically significant
4. Sees: **Effect Size: -3.2pp** — ML is 3.2 percentage points better
5. Sees: Hierarchy Breakdown by Region — Americas and EMEA are strong, APJ is mixed
6. **Conclusion:** "ML is ready for Americas and EMEA. APJ needs per-channel review before switching."

### Forecast Analyst
1. Opens dashboard, selects SubRegion: ANZ, Channel: Voice
2. Sees: **ML Wins: 4, Manual Wins: 9** — Manual is clearly better
3. Looks at weekly time series — ML had 2 very bad weeks that dragged down its average
4. Checks Q2 — The model assigned to ANZ Voice (V3_6_Prophet) has a mediocre composite score
5. **Conclusion:** "The model for ANZ Voice needs retraining or replacement. I'll flag this for the data science team."

---

## 9. Non-Negotiable Principles

These principles are **permanent** and must survive any future refactoring, redesign, or team handover:

1. **Mathematical algorithms are immutable. Business policies are configurable.** WAPE, Wilcoxon, and the aggregation method are fixed. Confidence thresholds, scoring weights, and display thresholds can be tuned.
2. **Every displayed number traces to a typed evidence source.** No number should appear on the dashboard without a corresponding formula in the Excel validation sheet.
3. **If evidence is weak, recommend nothing.** Suppressed recommendations are omitted entirely, never softened.
4. **The system never claims causation.** "Observed association" yes. "Because" no.
5. **WAPE is always computed by summing absolute errors and dividing by total actuals.** Never by averaging child WAPEs.
6. **The hierarchy is sacred.** Numbers at a parent level must be derivable from the children's raw errors and actuals.
7. **Confidence is visual, not textual.** A colored chip, not a footnote.
8. **Page 1 stands alone.** The Executive Overview must answer the core question without requiring navigation.
9. **Volume weighting is implicit, not optional.** The aggregation method ensures that high-volume queues naturally dominate the parent's WAPE.
10. **The four business questions are permanent.** They may be enhanced but never removed or replaced.

---

## 10. Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Only 13 weeks of actuals | Statistical power is limited; Wilcoxon may return "Inconclusive" for many slices | Display confidence prominently; suppress weak recommendations |
| No external causal data | Cannot explain WHY accuracy changed in a specific week | Use observational language only |
| ~360 queues across 14 sub-regions | Some sub-regions have very few queues (e.g., "Multiple AMER SubRegions" has 1) | Small-sample slices flagged with warnings |
| Single ML forecast per queue | The dashboard evaluates the ML system as a whole, not individual model selection | Q2 provides model-level detail for optimization |
| Static snapshot | Dashboard reflects one evaluation run, not real-time data | Clearly display evaluation period and generation timestamp |

---

## 11. File Reference

| File | Purpose |
|---|---|
| `app.py` | CLI entry point — loads data, runs pipeline, triggers dashboard generation |
| `generate_dashboard.py` | Mathematical engine — computes all WAPE calculations and chart data |
| `create_formula_excel_master.py` | Excel validation generator — creates SUMIFS-based proof sheet |
| `dashboard/index.html` | Dashboard UI — HTML/CSS/JS with Chart.js visualizations |
| `dashboard/data/report.json` | Pre-computed data payload — all slices, all chart data |
| `sample_data/Final_data.xlsx` | Source dataset — 35,640 rows x 45 columns |
| `handoff.md` | Previous handover document — architectural discoveries and frozen decisions |
| `ultimate_handover.md` | This document |
