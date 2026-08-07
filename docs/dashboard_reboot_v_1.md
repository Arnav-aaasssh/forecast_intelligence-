# Enterprise Forecast Decision Intelligence Platform
# Version 2.0 — Master Implementation Blueprint

**Document type:** Implementation-ready architectural blueprint (no code). Written so a coding-focused model can execute directly without inventing architecture, formulas, or workspace organization.
**Core metric standard:** WAPE (Weighted Absolute Percentage Error) is used throughout, in place of the Adherence formula shown in the reference screenshots — WAPE is already the metric this platform's Model Champion and Strategy Assessment modules are built on, and using one formula everywhere removes a class of "why do these two pages disagree" questions before they can occur.

---

## 1. Executive Summary

The platform's current implementation computes Manual-vs-ML performance and model quality at a **pooled, top-down level**: volumes are summed across whatever segments a filter selects, and WAPE is recalculated once on that pooled total. This is fast and simple, but it is also **statistically unsound** for a business with 360 independently-forecasted queues of wildly different size and difficulty — a small number of high-error, high-volume queues can flip the verdict for an entire region even when the overwhelming majority of that region's queues tell the opposite story. This is not a hypothetical risk: it was directly observed in this dataset (see Section 3) — the APJ region's pooled numbers say "ML barely wins," while 5 of its 6 sub-regions individually say "Manual wins clearly," because one high-error, high-volume sub-region (CCC) dominates the pooled total.

Version 2 replaces this with a **bottom-up aggregation framework**: WAPE and the Manual/ML verdict are computed independently for every queue, every week, first. Everything above that — sub-region, region, global — is a *rollup of queue-level verdicts*, never a recalculation from re-pooled volumes. The dashboard is redesigned around this atomic unit: a hierarchical, expandable investigation workspace (Region → Sub-Region → Country → Offering → Channel → Queue) replaces the current flat, single-level Strategy Assessment page, while preserving the existing visual identity, confidence-tier philosophy, and evidence-first design language in full.

---

## 2. Current State Assessment

**Strengths to preserve:**
- Evidence-first design language (Observation → Evidence → Conclusion → Decision Support), confidence tiers including the Inconclusive state, and the navy/teal/amber visual system are all validated and should not change.
- The existing four-question structure (Strategy Assessment, Model Champion, Business Context, Anomaly Detection) reflects a genuinely correct analytical sequence and is retained as the backbone of the workspace.
- Root-cause decomposition (segment deviation vs. its own historical baseline) is methodologically sound and reusable as-is.

**Weaknesses this version must fix:**
- **Top-down pooling hides reversals.** Aggregating volume first and recalculating WAPE at the top can produce a verdict that contradicts the majority of the underlying queues (Section 3's APJ/CCC case).
- **One global "champion" model** ignores that different queues, sub-regions, and channels each favor different models — a single global answer is often nobody's actual best choice.
- **No drill-down hierarchy.** Filters exist, but there's no way to expand from "Region" down through "Sub-Region → Country → Offering → Channel → Queue" while keeping analytical context — investigating a finding currently means re-filtering from scratch on a different page.
- **Excess navigation for a single investigation.** Moving from a summary finding to its supporting queue-level evidence currently requires switching pages and re-selecting filters, rather than expanding in place.
- **No persistent classification tagging.** Queues are judged one WAPE-comparison at a time; there's no standing label (e.g., "this queue reliably favors ML") that would let a planner scan a large hierarchy quickly.

---

## 3. Dataset Impact Analysis

**Hierarchy structure (confirmed, not assumed):** every one of the 360 `Forecast_Name` queues maps to **exactly one** combination of Region (3) → Sub-Region (14) → Country (47) → Offering (3) → Channel (5). This is a clean, non-overlapping tree — no queue spans more than one branch — which means hierarchy rollups are well-defined with no ambiguity about double-counting or split attribution.

**The concrete reversal case this framework must handle correctly:**

| Level | Manual WAPE | ML WAPE | Verdict |
|---|---|---|---|
| APJ Region (pooled) | 19.93% | 19.65% | ML (barely) |
| ANZ | 13.66% | 16.13% | **Manual** |
| CCC | 34.39% | 26.50% | ML |
| IN | 8.59% | 13.06% | **Manual** |
| JPN | 12.61% | 17.80% | **Manual** |
| KR | 23.59% | 27.62% | **Manual** |
| SA | 18.37% | 20.15% | **Manual** |

Five of six APJ sub-regions favor Manual; the pooled region-level number says ML, because CCC's exceptionally poor accuracy (34%+ error either way) combined with its size drags the pooled total. **Any redesigned methodology must reproduce "Manual wins in APJ" as the honest, count-based verdict, while still surfacing CCC's pooled dominance as a separate, visible fact** — hiding either side of this is a failure state.

**Only 13 of 99 weeks carry realized actuals** (unchanged from prior versions) — every queue-level WAPE, classification, and rollup in this blueprint is computed strictly on those 13 weeks, exactly as established previously. Per-queue historical baseline columns (`Mean (Hist. Contacts)`, `Std Dev (Hist. Contacts)`) exist at the same one-value-per-queue granularity as the hierarchy fields, so they can be attached to any node in the hierarchy without ambiguity.

---

## 4. Bottom-Up Aggregation Framework

This is the central methodological change. Three levels, strictly separated:

**Level 0 — Queue-Week (the atomic unit, computed once, never recomputed downstream).**
For every (Queue, Week) pair with a realized actual:
```
Manual_WAPE(q,w) = |Manual_Forecast − Actual| / Actual
ML_WAPE(q,w)     = |ML_Forecast − Actual| / Actual
Winner(q,w)      = "ML" if ML_WAPE(q,w) ≤ Manual_WAPE(q,w) else "Manual"
Within_Tolerance_ML(q,w)     = ML_WAPE(q,w) ≤ 10%
Within_Tolerance_Manual(q,w) = Manual_WAPE(q,w) ≤ 10%
```
This table is the single source of truth. Every other number in the platform — Strategy Assessment, Model Champion, Business Context, Anomaly Detection — is derived from it, never from a separately re-pooled calculation. This closes the door on the four modules ever silently disagreeing with each other.

**Level 1 — Queue Rollup (across all valid weeks, for one queue).**
```
Queue_WAPE_Manual = sum(|Manual_Forecast − Actual|) / sum(Actual)     [volume-weighted across that queue's own weeks]
Queue_WAPE_ML     = sum(|ML_Forecast − Actual|) / sum(Actual)
Weeks_ML_Wins_Pct = count(Winner = "ML") / count(valid weeks)
Classification:
    "Strong ML" if Weeks_ML_Wins_Pct ≥ 60%
    "Hybrid"    if 40% ≤ Weeks_ML_Wins_Pct < 60%
    "Manual"    if Weeks_ML_Wins_Pct < 40%
    "Insufficient Data" if valid weeks < 8   [overrides the above; see Section 5]
```
Note the volume-weighted queue-level WAPE and the win-count-based classification are **two different, complementary numbers, both kept** — WAPE tells you *how big* the error is; classification tells you *how often* one method wins. A queue can have a close WAPE gap but a lopsided win count, or vice versa, and both facts matter.

**Level 2+ — Hierarchy Rollup (Country → Sub-Region → Region → Global), computed two ways, both always shown:**
```
Count-Based Rollup   = % of child queues classified "Strong ML" (or "Manual", etc.) — every queue counts equally, regardless of size
Volume-Weighted Rollup = each queue's classification weighted by its share of total Actual volume at that node
```
**Why both, not one:** the count-based view answers "how broadly is one method preferred across our operational footprint" (useful for a regional head deciding a general policy); the volume-weighted view answers "which method matters more for the bulk of our actual business volume" (useful for a capacity-planning decision). Collapsing these into a single number is exactly the mechanism that produced the APJ/CCC reversal — a single pooled WAPE is implicitly a volume-weighted, error-magnitude-based statistic that silently ignores how many queues actually prefer each method. Neither lens is "more correct"; they answer different business questions, so both must be visible simultaneously, not toggled with one hidden by default.

**Fairness and decision-quality rationale:** a low-volume queue's verdict is never drowned out in the count-based rollup, so a planner scanning "how many of my queues prefer Manual" gets an honest operational picture rather than one dominated by whichever queue happens to be largest. The volume-weighted rollup is retained precisely because business impact does scale with volume — but it is now an explicit, separate, labeled number rather than the *only* number, which is what allowed it to silently misrepresent the region in the current implementation.

**Assumptions/limitations to document, not hide:** the 60%/40% classification thresholds are a policy choice (configurable, not hard-coded, per the platform's existing separation of mathematical fact from business policy); an 8-week minimum for classification is a judgment call balancing statistical caution against not wanting to mark most of a 13-week dataset "insufficient" (see Section 5 and Section 24 for how this is monitored).

---

## 5. Statistical Methodology

- **Metric:** WAPE throughout (not Adherence), for consistency with the rest of the platform, per instruction.
- **Tolerance band:** ±10% WAPE, matching the platform's existing Hit10 concept — reused, not reinvented.
- **Classification priority when a queue sits exactly on a boundary:** Strong ML → Hybrid → Manual, in that priority order (i.e., ties resolve toward the more favorable-to-ML label first, then Hybrid, matching the reference pattern's own stated tie-break rule, adopted here for consistency with a scheme planners may already be familiar with).
- **Minimum sample size for classification:** a queue needs **≥ 8 of the 13 valid weeks** to receive a Strong ML/Hybrid/Manual label; below that, it is labeled **"Insufficient Data"** and excluded from both count-based and volume-weighted rollups (not silently dropped — shown as its own explicit bucket at every hierarchy level, consistent with the platform's "sections condense, never disappear" rule).
- **Confidence tiers (existing High/Medium/Low/Inconclusive system) remain, applied at the rollup level**, not the individual queue level — a single queue's classification is a descriptive label, not a statistical claim; confidence tiers apply when a *rollup* (e.g., "Region X favors ML") is being asserted as a decision-worthy finding.

---

## 6. Analytics Redesign

All four existing modules are re-pointed to consume the Level-0 queue-week table as their sole input, rather than each computing its own pooled aggregate independently:

- **Strategy Assessment** consumes Level 0/1/2 rollups directly (this document's primary subject).
- **Model Champion** is re-scoped to compute its composite score (WAPE / Bias / Max-Error / Hit10 — unchanged formulas) **within whichever hierarchy node is currently selected**, not only globally — so "best model" becomes "best model for this Region / Sub-Region / Channel," matching the concrete finding that ANZ, JPN, and KR each have a different best-performing model.
- **Business Context** attaches each queue's own historical baseline columns to whichever node is selected, so the realized-vs-planned and below-baseline views can be read at any hierarchy depth, not only globally.
- **Anomaly Detection**'s existing segment-level z-score logic already operates at the queue grain — no formula change needed, only exposure through the same hierarchy navigation as the other three modules.

---

## 7. Dashboard Philosophy

The dashboard remains a **decision-support workspace**, not a report. The existing visual theme, color palette, typography, and card system are preserved without change, per instruction. What changes is the *organizing principle*: investigations, not fixed pages. A user should be able to start from a top-level finding and drill into its supporting evidence **without leaving the page or losing the filter context that got them there** — this is the single biggest UX gap identified in Section 2.

---

## 8. Information Architecture

```
Executive Overview        (always global/unfiltered synthesis + RAG status — unchanged position, updated content per Section 12)
Strategy Assessment       (NEW: hierarchy drill-down workspace — Section 13)
Model Champion            (hierarchy-scoped — Section 14)
Business Context          (hierarchy-scoped — Section 15)
Anomaly Detection         (unchanged structurally, now reachable from any hierarchy node — Section 16)
```
Global filters (Section 11) sit persistently above all five, so a Region/Sub-Region selection made anywhere carries into every workspace without re-selection.

---

## 9. UX Strategy

- **Expand-in-place over navigate-away.** Clicking a hierarchy row (e.g., "APJ") expands its children (ANZ, CCC, IN, JPN, KR, SA) inline, with an "Expand All / Collapse All" control — modeled on the reference screenshots' hierarchy table pattern, adapted to this platform's card/table visual language rather than copied wholesale.
- **Selecting a node updates supporting charts in place**, not on a new page — the weekly trend chart, tolerance-distribution chart, and root-cause panel all re-render for whatever node is currently selected, keeping the user's place in the investigation.
- **Minimize scrolling:** KPI strip and the hierarchy table's first two levels (Region, Sub-Region) are visible above the fold by default; deeper levels (Country, Offering, Channel, Queue) expand downward on demand rather than being pre-expanded.
- **A persistent "Definitions" reference** (glossary of every metric and formula, always one click away) is adopted from the reference screenshots as a genuinely good, reusable pattern — planners frequently need to confirm exactly what a metric means mid-investigation, and burying that in a separate document defeats the purpose.

---

## 10. Workspace Specifications — Strategy Assessment (the primary redesign target)

**Top strip (always visible):**
- Total Queues Evaluated · Total Valid Queue-Weeks (Actual ≠ blank) · Count-Based "% Queues Strong ML" · Volume-Weighted "% Volume Favoring ML" · Classification legend (Strong ML / Hybrid / Manual / Insufficient Data, with counts)

**Hierarchy table (the main investigation surface):**
- Columns: Region / Sub-Region / Country / Offering / Channel / Queue name → Valid Weeks → Manual WAPE → ML WAPE → % Weeks ML Wins → Classification chip
- Expand/collapse per row and globally; a "swap dimension order" control (e.g., Sub-Region ↔ Offering) lets a planner re-slice the same tree by a different business dimension without rebuilding the query, matching the reference pattern
- Sortable on every numeric column

**Weekly trend panel (updates based on whichever row is currently selected):**
- Dual-line WAPE-over-time chart (Manual = red, ML = green, per the established convention), with a shaded ±10% tolerance band, so breaches are visible directly on the trend rather than requiring a separate tolerance-distribution chart to notice them
- A supporting tolerance-distribution segmented bar (buckets: ≤10%, 10–15%, 15–20%, 20–30%, >30%) for the selected node, showing the full error spread rather than a single average

---

## 11. Global Filter Strategy

**Filters:** Region, Sub-Region, Country, Offering, Channel, Forecaster, Fiscal Year, Fiscal Month, Fiscal Week — plus a **"Review by: Fiscal Week / Fiscal Month"** toggle (adopted from the reference pattern) that re-buckets the same underlying weekly data to a coarser time grain without recomputation of the underlying queue-week table.

**Persistence and scope:** filter state persists across all five workspaces (Executive Overview remains the sole exception, per its "stands alone" mandate). Selecting a hierarchy row inside Strategy Assessment **sets** the global filter to that node — so clicking into "ANZ" and then switching to Model Champion lands on ANZ's model leaderboard automatically, closing the current gap where switching pages loses context.

**Analytical impact:** filters narrow which rows of the Level-0 queue-week table are included in every downstream rollup; they never change which formula is used — this is the same principle already established (filters change scope, never methodology).

---

## 12. Executive Overview Redesign

- Replace the single global "Manual X – ML Y week split" KPI with the **count-based classification distribution** ("Strong ML in N% of queues, Manual preferred in M%, Hybrid in the rest") — this is the number that would have correctly represented APJ, where the pooled figure would not have.
- **Add an automatic hierarchy-disagreement flag:** if a parent node's pooled verdict differs from the majority verdict of its own children (the APJ/CCC pattern), surface this explicitly as a standing risk callout — "Region-level pooled result differs from the majority of its Sub-Regions; a small number of high-volume, high-error queues may be driving the pooled figure" — turning the manual detective work done for APJ into an automated, permanent check.
- RAG banner, storyline strip, and plain-language framing established previously are retained unchanged in tone and position.

---

## 13. Strategy Assessment Redesign

Fully specified in Sections 4 and 10. Summary of what changes from the current page: replaces the flat 13-week Manual-vs-ML line with the hierarchy drill-down workspace; replaces the single win-count KPI with count-based and volume-weighted classification distributions shown side by side; adds the queue-level classification chip system; adds the swap-dimension and expand/collapse controls; retains the existing weekly WAPE trend chart concept but scopes it to whichever hierarchy node is selected rather than only the global total.

---

## 14. Model Champion Redesign

- **Scope parameter added:** every existing calculation (composite score, eligibility by week-coverage, confidence tier) now runs against whichever hierarchy node is currently selected via the global filter, not only "all data."
- **Metrics, weighting, and eligibility rule are unchanged** (WAPE 40% / Bias 25% / Max-Error 15% / Hit10 20%; ≥8-of-13-week coverage) — these were already validated; only their scope changes.
- **Tie-breaking:** unchanged from the existing composite-score ranking (highest score wins; ties are vanishingly unlikely given continuous scoring, so no additional rule is introduced).
- **Confidence:** the existing champion-vs-runner-up significance check now runs per scope — a champion that's statistically distinguishable globally may not be within a single small sub-region, and the UI must show this rather than implying uniform confidence everywhere.

---

## 15. Business Context Redesign

- Historical baseline (`Mean`/`Std Dev (Hist. Contacts)`) is attached to whichever hierarchy node is selected — a Region-level view sums its queues' historical means; a single-queue view uses that queue's own baseline directly, with no recalculation of the historical statistic itself (it is a stored, per-queue value, never recomputed from the 13-week sample, avoiding the small-sample circularity already identified and fixed in a prior version).
- **Avoid misleading comparisons:** never blend the "realized" and "planned/forecast" volume tracks into one line (already established); extend the same discipline to hierarchy rollups — a Region's "historical baseline" must be the sum of its queues' own independently-set baselines, never a baseline recomputed from the Region's pooled 13-week actuals.

---

## 16. Root Cause Analysis Redesign

Investigation flow, using the ANZ-Email finding as the template case:

```
Observation:        "ANZ is classified Manual overall, but is this true in every channel?"
Evidence:            Channel-level WAPE table for ANZ (Voice, Chat, Email) — Email shows Manual winning even against ANZ's own best individual model
Supporting Analytics: Best-model-per-channel comparison, historical baseline check for the Email queue specifically
Conclusion:          "Manual is genuinely better for ANZ-Email specifically, not just overall"
Recommended Investigation: "Check whether this holds for other regions' Email channels, or is specific to ANZ"
```
This flow is surfaced as a guided panel attached to any hierarchy node showing a Hybrid or borderline classification — those are exactly the nodes where a channel-level or model-level breakdown is likely to change the operational recommendation, so the workflow proactively suggests drilling there rather than waiting for the user to think to ask.

---

## 17. Visualization Strategy

| Chart | Used for | Why this chart, not another |
|---|---|---|
| Dual-line WAPE trend + tolerance band | Weekly Manual vs ML at any selected node | Shows *when* breaches occur, which a single average cannot; the shaded band makes "within tolerance" a visual fact, not a mental calculation |
| Segmented tolerance-distribution bar | Full error spread for a node | An average hides spread; this shows how many weeks were mildly off vs. badly off, changing the practical read even at equal average WAPE |
| Expandable hierarchy table (not treemap/sunburst) | Primary drill-down surface | Planners need exact numbers and sortability more than a decorative area-based visual; a table supports both, a treemap supports neither well |
| Classification chips (not a chart) | Quick categorical read at every level | Three categories plus Insufficient Data is a labeling problem, not a visualization problem — a chip is faster to scan than a chart for this |
| Triple-line Actual/ML/Manual volume chart | Business Context, per node | Planners think in volume, not just error percentage; showing the raw forecast lines against reality is more directly interpretable than an error-only chart |

No chart is included for decorative reasons; each is justified against a specific reading task above.

---

## 18. UI Component Inventory

- KPI strip cards (existing component, reused)
- Classification legend chips (new: Strong ML / Hybrid / Manual / Insufficient Data)
- Expandable hierarchy table with sort, expand/collapse, and swap-dimension controls (new)
- Weekly WAPE trend chart with tolerance-band shading (extends existing chart component)
- Tolerance-distribution segmented bar (new)
- Global filter bar, extended with Country/Offering/Channel/Forecaster and the Fiscal Week/Month toggle (extends existing component)
- RAG banner and storyline strip (existing, unchanged)
- Root-cause guided panel (new, per Section 16)
- Persistent Definitions/glossary tab (new, adopted from reference pattern)

---

## 19. Backend Changes Required

- `compute_queue_week_metrics()` — new, produces the Level-0 atomic table (Queue × Week × Manual_WAPE × ML_WAPE × Winner × tolerance flags).
- `compute_queue_rollup()` — new, produces Level-1 per-queue classification and volume-weighted WAPE.
- `compute_hierarchy_rollup(node, level, weighting)` — new, generic rollup function usable at any hierarchy depth, returning both count-based and volume-weighted results; called on-demand for whichever node the user selects, rather than exhaustively precomputed for every possible node (see Section 21 for why).
- Extend Model Champion, Business Context, and Anomaly Detection module signatures to accept a `scope` (hierarchy node) parameter, sourced from the same Level-0 table.
- Retire any pooled-recompute logic that currently recalculates WAPE directly from re-summed volumes at a filtered level — this is the specific pattern being replaced.

---

## 20. Frontend Changes Required

- New expandable hierarchy table component (Section 18) — the single largest new UI element.
- New classification chip component, styled within the existing color system (Strong ML = teal/green, Manual = rust/red, Hybrid = amber, Insufficient Data = gray, consistent with established conventions).
- Extend the existing trend-chart component to accept and render a tolerance band.
- New tolerance-distribution segmented bar chart component.
- New Fiscal Week/Month toggle and swap-dimension control, wired to re-render the hierarchy table without a full page reload.
- New Definitions/glossary panel, populated from the formula table in Section 5 and this document's terminology throughout.

---

## 21. Data Flow

```
Raw dataset (35,640 rows)
        ↓
Level 0: Queue-Week metrics table  (computed once; ~360 queues × 13 weeks ≈ 4,680 rows — small enough to ship to the client in full)
        ↓
Level 1: Queue rollup (classification, volume-weighted WAPE) — derived from Level 0 by a simple groupby, computed on-demand (client-side or server-side, either is cheap at this size)
        ↓
Level 2+: Hierarchy rollup (any node, any level, count-based and volume-weighted) — derived from Level 1 by another groupby along whichever hierarchy path is selected
        ↓
Dashboard renders whichever node is currently selected, always tracing back to the same Level 0 table
```
Because Level 0 is small (~4,680 rows), there is no need to exhaustively precompute every possible hierarchy-node combination as earlier versions did for global filters (which required 225 precomputed slices) — the aggregation from Level 0 upward is cheap enough to compute live for whatever node the user picks, which also guarantees perfect consistency (no risk of a precomputed slice going stale relative to the atomic table).

---

## 22. Implementation Dependencies

1. Level 0 queue-week table must exist and be validated before any rollup logic is built.
2. Classification thresholds (60%/40%, 8-week minimum) must be finalized as configuration values before Level 1 rollup is implemented, since they are policy, not derived facts.
3. Hierarchy metadata integrity (confirmed in Section 3: every queue maps to exactly one path) must be re-validated automatically on every data refresh, not just once at design time — a future data version could introduce a queue that violates this, which would silently break the rollup.
4. The APJ/CCC reversal case (Section 3) should be used as a standing regression test — if a future implementation change ever makes the pooled and count-based views agree on this case, that is a signal something in the aggregation logic broke, not that the discrepancy resolved itself.

---

## 23. Recommended Development Order

1. Build and validate the Level 0 queue-week metrics table against the known APJ/CCC and ANZ-channel cases by hand.
2. Build Level 1 queue rollup and classification; re-validate the same known cases.
3. Build the generic Level 2+ hierarchy rollup function (count-based and volume-weighted); confirm it reproduces "Manual wins in APJ" (count-based) while still surfacing CCC's pooled dominance separately.
4. Build the Strategy Assessment hierarchy-table workspace UI on top of the now-validated backend.
5. Extend Model Champion to accept a scope parameter and re-validate against the known ANZ/JPN/KR best-model findings.
6. Extend Business Context to hierarchy-scoped historical banding.
7. Build the Root Cause guided panel (Section 16).
8. Extend global filters to persist across all workspaces and to set scope from a selected hierarchy row.
9. Build the Executive Overview's automated hierarchy-disagreement flag last, since it depends on every rollup level already being correct.

---

## 24. Risks and Mitigations

- **Risk:** count-based and volume-weighted rollups disagree for a given node. **This is expected, not a bug** — mitigate by always displaying both, never suppressing one, with a short inline explanation of why they can differ (mirroring Section 4's rationale).
- **Risk:** the 8-week minimum and 60%/40% thresholds are judgment calls that could mis-classify edge cases. **Mitigate** by exposing them as configurable policy values (not hard-coded), and by monitoring how many queues land in "Insufficient Data" or exactly on a boundary after each data refresh — a sudden jump in either count is a signal to review the thresholds, not silently accept them.
- **Risk:** a future dataset version could introduce a queue spanning more than one hierarchy path, breaking the clean-tree assumption Section 3 confirmed. **Mitigate** with an automated integrity check on every data load, failing loudly rather than silently mis-aggregating.
- **Risk:** users familiar with the old single pooled Manual-vs-ML number may find two rollup numbers confusing at first. **Mitigate** with the Definitions panel (Section 9/18) and a short inline explanation directly on the KPI strip, not a separate help document.

---

## 25. Acceptance Criteria

- Every queue has an independently computed WAPE and classification, traceable to Level 0 with no pooled-recompute shortcuts remaining anywhere in the codebase.
- Hierarchy rollups are available at every level (Country, Sub-Region, Region, Global) via both count-based and volume-weighted lenses, computed live from Level 0/1, not from stale precomputed slices.
- The APJ/CCC case reproduces exactly as documented in Section 3 (count-based: Manual favored in 5 of 6 sub-regions; pooled: ML narrowly favored) when checked by hand against the implementation.
- The ANZ-Email case (Manual beats even the best individual model for that specific channel) is reproducible via the Root Cause workflow without custom one-off analysis.
- Drill-down from Region to Queue requires no full page reload and preserves the user's place in the investigation.
- Global filters persist across Strategy Assessment, Model Champion, Business Context, and Anomaly Detection (Executive Overview remains the sole, intentional exception).
- Existing visual theme, color palette, and confidence-tier system are unchanged in appearance.
- The Definitions/glossary panel is reachable from every workspace in one click.
