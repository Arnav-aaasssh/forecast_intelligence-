# Bottom-Up Aggregation & Dashboard Redesign
# Execution Plan v2 — Full Detail (Backend + Elaborate UI Architecture)

**Change from the prior version of this plan:** the ≥8-of-13-valid-weeks minimum-sample gate for queue classification is **removed**. A queue is classified using whatever valid weeks it has, down to a single week. The only remaining "no label possible" state is genuinely **zero valid weeks** (a queue with no realized actuals at all — a data-availability fact, not a statistical judgment call). Checked against the real data before writing this: **347 of 360 queues already have all 13 weeks; only 1 queue has fewer than 8 (it has 4); zero queues have 0.** So in practice this change reclassifies exactly one queue from "Insufficient Data" to a real label — worth stating plainly rather than implying a bigger effect than it has. The mechanism matters for correctness and for any future data refresh where low-coverage queues could be more common, even though today's impact is small.

---

## PART A — BACKEND CHANGES (elaborate, function-by-function)

### A.1 — Revised classification function

**Before (removed):**
```python
MIN_VALID_WEEKS = 8
...
if n < MIN_VALID_WEEKS:
    cls = 'Insufficient Data'
elif ml_win_pct >= 0.60:
    cls = 'Strong ML'
...
```

**After:**
```python
CLASSIFICATION_ML_HIGH = 0.60
CLASSIFICATION_ML_LOW  = 0.40

def classify_queue(n_valid_weeks: int, ml_win_pct: float) -> str:
    if n_valid_weeks == 0:
        return 'No Data'                      # genuinely no realized weeks -- a data fact, not a judgment call
    if ml_win_pct >= CLASSIFICATION_ML_HIGH:
        return 'Strong ML'
    if ml_win_pct >= CLASSIFICATION_ML_LOW:
        return 'Hybrid'
    return 'Manual'
```

**Rationale for keeping `'No Data'` as a distinct, separate state from the classification bands:** this is not a re-introduction of the removed gate under a new name. The removed rule was a *statistical caution* ("we have data, but not enough to trust it") — a judgment call. `'No Data'` is a *factual* state ("there is nothing to compute from") — not a judgment call, just an honest description of what's in the table. These are categorically different, and collapsing them back together would silently reintroduce the same gate. Zero queues hit this state today, but the function must handle it without dividing by zero.

**Consequence for `compute_queue_rollup()` (Phase 2 of the prior plan):** delete the `MIN_VALID_WEEKS` constant and the branch that used it; replace with a direct call to `classify_queue()`. No other signature changes — the function still returns the same columns (`n_valid_weeks`, `ml_win_pct`, `classification`), only the value space of `classification` changes (`'Insufficient Data'` → replaced by `'No Data'`, now meaning something narrower and rarer).

**Consequence for `compute_hierarchy_rollup()` (Phase 3):** the line `eligible = merged[merged['classification'] != 'Insufficient Data']` becomes `eligible = merged[merged['classification'] != 'No Data']`. Because this state is now expected to be empty or near-empty (vs. potentially 13 queues under the old rule, since some queues had 9-12 weeks that would've stayed classified anyway — recheck: actually under the old rule only 1 queue was excluded, so this changes barely anything numerically, but the *semantic* meaning of the excluded bucket is now correct and narrower).

**Consequence for confidence tiers at the rollup level:** a rollup built partly from single-week queue classifications is *inherently* less statistically robust than one built from full-13-week queues, even though both now receive a label. This must **not** be silently hidden. Add a new derived field at Level 1:

```python
def classification_reliability(n_valid_weeks: int) -> str:
    if n_valid_weeks >= 10:
        return 'Stable'
    if n_valid_weeks >= 4:
        return 'Provisional'
    return 'Single-Week'   # 1-3 valid weeks: label exists, but treat as a very early read
```

This is a **separate field from `classification`**, never blended into it — a queue can be `"Strong ML"` and `"Single-Week"` at the same time, and the UI must show both, not average them away. This is the direct mechanism that keeps "we removed the hard gate" from silently becoming "we now show unreliable labels as if they were solid ones."

### A.2 — Full revised `compute_queue_rollup()`

```python
def compute_queue_rollup(qw: pd.DataFrame) -> pd.DataFrame:
    def _agg(g):
        n = len(g)
        ml_win_pct = (g['Winner'] == 'ML').mean() if n > 0 else None
        manual_wape = g['Manual_AbsErr'].sum() / g['Actual_Offered'].sum() if n > 0 else None
        ml_wape     = g['ML_AbsErr'].sum()     / g['Actual_Offered'].sum() if n > 0 else None
        return pd.Series({
            'n_valid_weeks': n,
            'ml_win_pct': ml_win_pct,
            'manual_wape': manual_wape,
            'ml_wape': ml_wape,
            'classification': classify_queue(n, ml_win_pct if ml_win_pct is not None else 0),
            'reliability': classification_reliability(n),
        })
    return qw.groupby('Forecast_Name').apply(_agg).reset_index()
```

### A.3 — Hierarchy rollup: reliability rolls up too

`compute_hierarchy_rollup()` must also report, per node, **what share of its child queues are Single-Week / Provisional / Stable** — not just the classification distribution. This lets a Region-level card say something like "8 of 9 contributing queues have a stable, full-history read; 1 is a single-week early signal" rather than silently presenting all contributing queues as equally trustworthy.

```python
def compute_hierarchy_rollup(queue_rollup, hierarchy_map, level, node=None):
    merged = queue_rollup.merge(hierarchy_map, on='Forecast_Name')
    if node:
        merged = merged[merged[level] == node]
    eligible = merged[merged['classification'] != 'No Data']

    def _rollup(g):
        count_based = g['classification'].value_counts(normalize=True).to_dict()
        weighted = (g.groupby('classification')['total_volume'].sum() / g['total_volume'].sum()).to_dict()
        reliability_mix = g['reliability'].value_counts(normalize=True).to_dict()
        return pd.Series({
            'count_based_pct': count_based,
            'volume_weighted_pct': weighted,
            'reliability_mix': reliability_mix,
            'n_queues': len(g),
        })

    if node:
        return _rollup(eligible).to_dict()
    return eligible.groupby(level).apply(_rollup).reset_index()
```

### A.4 — Edge cases explicitly handled

| Case | Handling |
|---|---|
| Queue with 0 valid weeks | `classification = 'No Data'`, `reliability` field is `None`/not applicable, excluded from all rollups (same as before, just correctly labeled now) |
| Queue with exactly 1 valid week | Gets a real classification (`Strong ML`/`Hybrid`/`Manual` based on that single week's winner — `ml_win_pct` is either 0% or 100%), `reliability = 'Single-Week'` |
| Queue with 4-9 valid weeks | Classified normally, `reliability = 'Provisional'` (4-9) — note the boundary at 10 is a policy choice, documented as configurable, same as the classification thresholds themselves |
| Hierarchy node whose children are entirely Single-Week | Rollup still computes (no gate blocks it), but the `reliability_mix` will show 100% Single-Week — this is the signal a user needs, not a suppressed result |

### A.5 — JSON schema change (`master_data_v2.json`)

`queue_rollup` array: each object gains one new field, `reliability` (string: `'Stable'`/`'Provisional'`/`'Single-Week'`/`null`). `hierarchy_rollup` responses (computed client-side per Phase 3/4 of the prior plan) gain `reliability_mix` alongside the existing `count_based_pct` and `volume_weighted_pct`. No fields are removed; this is purely additive, so nothing already shipped in earlier phases breaks.

---

## PART B — UI ARCHITECTURE (elaborate, component-by-component, page-by-page)

### B.1 — Page-level layout, Strategy Assessment (the primary redesign surface)

Reading top to bottom, this is the full vertical stack of the page, in order, with each zone's role:

```
┌─────────────────────────────────────────────────────────────┐
│ ZONE 1 — Global Header (UNCHANGED, existing component)       │
│   Platform title, evaluation period, record/model counts     │
├─────────────────────────────────────────────────────────────┤
│ ZONE 2 — Evidence Banner (UNCHANGED, existing component)      │
│   "13 of 99 weeks realized..." -- stays exactly as-is         │
├─────────────────────────────────────────────────────────────┤
│ ZONE 3 — Global Filter Bar (MODIFIED, existing component)     │
│   Sub-Region / Fiscal Year / Quarter dropdowns REMAIN         │
│   in their current position and styling.                     │
│   NEW: a read-only "Current Scope" pill appended to the       │
│   right of the Reset button, e.g. "Scope: APJ > ANZ" --       │
│   this reflects whatever hierarchy node is selected below     │
│   in Zone 5, and is REMOVABLE (click an × on the pill to      │
│   clear scope back to "All"). This is new UI, but it lives    │
│   inside the existing filter-bar container, not a new bar.    │
├─────────────────────────────────────────────────────────────┤
│ ZONE 4 — KPI Strip (MODIFIED CONTENT, same visual component)  │
│   4 cards, same size/style/position as today's Strategy       │
│   Assessment KPI row. CONTENT CHANGES:                        │
│     Card 1 (was "Weeks the Human Planner Got Closer"):        │
│        -> becomes "Queues Favoring the Human Planner"         │
│           value = count-based % of queues classified          │
│           "Manual" (at current scope)                         │
│     Card 2 (was "Weeks the AI/ML Model Got Closer"):           │
│        -> becomes "Queues Favoring the ML Model"               │
│           value = count-based % classified "Strong ML"        │
│     Card 3 (was "How Big Is the Gap"):                        │
│        -> becomes "Volume-Weighted Split"                      │
│           value = volume-weighted % favoring ML vs Manual,     │
│           shown as a single split value e.g. "38% by volume"  │
│     Card 4 (was "How Sure Are We" / confidence chip):          │
│        -> becomes "Data Reliability" showing the               │
│           reliability_mix as three small stacked segments      │
│           (Stable / Provisional / Single-Week) instead of a    │
│           single confidence chip -- this REPLACES the old      │
│           Inconclusive/Low/Medium/High chip IN THIS SPECIFIC   │
│           CARD ONLY. The Inconclusive/Low/Medium/High system   │
│           itself is NOT removed from the platform -- it still  │
│           governs Model Champion's champion-vs-runner-up       │
│           check and is unchanged there (Part B.4).             │
├─────────────────────────────────────────────────────────────┤
│ ZONE 5 — NEW: Hierarchy Table Workspace (entirely new)        │
│   Replaces the OLD "Weekly Winner — 13 Realized Weeks" strip  │
│   and the OLD donut/advantage-bar pair as the page's primary  │
│   content surface. Full spec in B.2.                          │
├─────────────────────────────────────────────────────────────┤
│ ZONE 6 — Node Detail Panel (new, but reuses existing charts)  │
│   Two side-by-side cards, same grid-2 layout already used     │
│   elsewhere in the platform:                                  │
│     Left card: the EXISTING weekly WAPE line chart component,  │
│       modified to add a shaded tolerance band (B.3) --         │
│       re-scoped to whichever node is selected in Zone 5.       │
│     Right card: the EXISTING evidence-table component          │
│       (Manual miss / ML miss / gap / sample size rows),        │
│       unchanged in structure, re-scoped to the selected node.  │
├─────────────────────────────────────────────────────────────┤
│ ZONE 7 — NEW: Tolerance Distribution Chart                    │
│   New stacked bar (B.3), placed below Zone 6, full width.      │
├─────────────────────────────────────────────────────────────┤
│ ZONE 8 — Root Cause Guided Panel (new, conditional)            │
│   Only rendered when the selected node's classification is    │
│   "Hybrid" or within 10 points of a boundary. Full spec B.5.   │
└─────────────────────────────────────────────────────────────┘
```

**What this means for what's REMOVED vs. RELOCATED vs. UNCHANGED, explicitly:**
- **Removed from this page entirely:** the win/loss donut chart and the per-week "margin of victory" diverging bar chart (from the current build). These answered "who won more weeks, globally" — a question the hierarchy table now answers more completely and at every level, not just globally. They are not moved elsewhere; they are superseded.
- **Relocated:** the win-strip (13 colored week cells) moves from being the page's second element to living **inside Zone 6**, as a third small component under the trend chart, but only rendered when the selected node is a single Queue (leaf-level) — at Region/Sub-Region levels there is no single "week strip" that means anything, since a Region contains many queues each with their own weekly pattern. This is a genuine behavior change: the win-strip becomes leaf-level-only, not always-visible.
- **Unchanged in position and behavior:** Zones 1–3 (header, evidence banner, filter bar container itself), and the overall card visual style (radius, border, shadow-on-hover) throughout.

### B.2 — Hierarchy Table Workspace (Zone 5), full component spec

**Visual structure**, one row per node, indentation signals depth:

```
[▾] Region: APJ                    12 queues   Manual: 42%  Strong ML: 33%  Hybrid: 25%   [chips: Manual bar dominant]
    [▾] Sub-Region: ANZ             3 queues   Manual: 67%  Strong ML: 33%  Hybrid: 0%
        [▾] Country: Australia      3 queues   ...
            [▸] Offering: Basic     1 queue    ...
                [ ] Channel: Voice  1 queue    Classification: Manual   Reliability: Stable
            [▸] Offering: Pro       2 queues   ...
    [▸] Sub-Region: CCC             (collapsed)
    [▸] Sub-Region: IN              (collapsed)
    ...
```

- **Expand toggle** `[▾]`/`[▸]`: a single triangle glyph per row, rotates on click (CSS transition, no new icon library needed — reuse the same triangle glyph already used for select-dropdown arrows elsewhere in the platform, for visual consistency).
- **Indentation:** 20px per depth level, consistent with standard tree-table conventions; row background alternates subtly (existing zebra-striping pattern from the Model Champion leaderboard table, reused here, not reinvented).
- **Columns, left to right:** Node name (with expand toggle and indentation) → # Queues (child count at that node, or "1 queue" at leaf) → Manual % (count-based) → Strong ML % (count-based) → Hybrid % (count-based) → a small horizontal **stacked bar** (not a number) visually showing the three percentages as proportional colored segments (red/green/amber, matching the platform's established Manual=red/ML=green convention, amber for Hybrid) — this bar is the fastest-scan element in the row, letting a user visually spot "this node leans Manual" without reading numbers first.
- **Reliability indicator:** a small dot or icon at the far right of each row (only meaningful at leaf/Queue level; at higher levels this becomes the `reliability_mix` mini-bar instead, three-segment, same visual pattern as the classification bar but in a muted gray/blue palette to visually distinguish "how much data" from "what the data says").
- **Row click behavior:** clicking anywhere on a row **other than the expand toggle** selects that node (sets `currentScope`), highlighting the row (background tint using the existing `--teal-soft` token) and triggering Zone 6/7/8 to re-render for that node — this is a single click, not double-click, and does not also expand/collapse (that's the separate toggle's job) so users can select a Region without being forced to also see its children.
- **Column sort:** clicking any percentage column header sorts all *currently visible* rows (respecting expand/collapse state) by that column — reuses the exact sort-arrow UI already present on the Model Champion leaderboard table headers.
- **Swap-dimension control:** a small dropdown positioned at the top-right of Zone 5 (not a separate toolbar), labeled "Group by:", options `Region → Sub-Region → Country → Offering → Channel` (default) or `Region → Offering → Channel → Sub-Region → Country` (swapped) — changing this re-renders the entire tree with the new grouping order, collapsing back to the default expand state (Region-level only) rather than trying to preserve expand-state across a structurally different tree.
- **"Expand All" / "Collapse All"** buttons sit beside the swap-dimension dropdown, same row, right-aligned — matching the position convention already used for similar controls in the reference-inspired pattern, adapted into this platform's existing button styling (the same pill-shaped secondary-button style already used for "Reset filters").

### B.3 — Modified/New Charts, exact specification

**Tolerance-band trend chart (Zone 6, left card) — modifies the EXISTING line chart component:**
- Same Chart.js `line` type, same two datasets (Manual = red line, ML = green line) as today.
- **New addition:** two additional invisible boundary datasets at +10% and −10% around each week's actual (or, simpler and recommended: a fixed horizontal band at ±10% WAPE, rendered via Chart.js's `fill` option between two flat reference lines) — shaded pale gray, `z-index` behind the two data lines, so breaches above/below the band are visually obvious without reading exact numbers.
- Title and axis labels update dynamically based on selected node: e.g., "Weekly WAPE — ANZ (3 queues, volume-weighted)" vs. "Weekly WAPE — ANZ Client Core Voice (single queue)" — the chart component takes a `nodeLabel` and `nodeType` (aggregate vs. leaf) prop and adjusts its own title text accordingly, not a static title.

**Tolerance-distribution stacked bar (Zone 7) — entirely new component:**
- Chart.js `bar`, `stacked: true`, one bar for Manual and one for ML (two bars total, side by side, not per-week — this summarizes the *whole selected node's* history into one distribution snapshot, complementing rather than duplicating the trend chart above it).
- Five stacked segments per bar: ≤10% (green), 10–15% (yellow-green), 15–20% (amber), 20–30% (orange), >30% (red) — a 5-step sequential-ish scale, reusing the platform's existing amber/rust family rather than introducing new hues, extended with two intermediate tones.
- Legend below the chart, horizontal, same style as existing chart legends elsewhere on the page.

### B.4 — Model Champion page: exact positional impact

**Nothing in Model Champion's existing layout moves.** The gauge, radar, leaderboard bar chart, family bar chart, and full table all stay in their current Zones/positions. The only change is **content scope**:
- A new small text line appears directly under the page's existing KPI strip (Zone 4 equivalent on that page), reading e.g. **"Scoped to: APJ > ANZ"** (or "Scoped to: All Regions" when no node is selected) — styled as a muted caption, not a card, so it doesn't compete visually with the existing KPI cards.
- The gauge, radar, and leaderboard recompute for whatever `currentScope` is active (Part A of the original plan, Phase 7) — visually, this looks like the exact same components, just showing different numbers/models when scope changes, with a brief cross-fade transition (200ms opacity) on the gauge and bar charts specifically, so a scope change reads as an update, not a jarring reset.
- The existing Inconclusive/Low/Medium/High confidence chip for "champion vs. runner-up" is **fully retained here, unchanged** — this is the one place in the platform where that specific four-tier system continues to operate exactly as before; it is not touched by the reliability-tier changes in Part A, which apply only to queue-level classification on the Strategy Assessment page.

### B.5 — Root Cause Guided Panel (Zone 8), exact structure

Only renders when `selectedNode.classification === 'Hybrid'` OR the node's `ml_win_pct` is within 10 percentage points of the 60%/40% boundaries. When rendered:

```
┌─ Root Cause Panel ─────────────────────────────────────────┐
│  ◆ This node is close to a tipping point                    │
│                                                               │
│  Observation:  [plain-language sentence, e.g. "ANZ overall  │
│                 favors Manual, but this is close for its     │
│                 Voice channel specifically."]                │
│                                                               │
│  [ Drill into Channel-level detail → ]  (button, navigates   │
│    by auto-expanding the hierarchy table to Channel level     │
│    for this node and re-selecting the most borderline child) │
└───────────────────────────────────────────────────────────┘
```
- Positioned full-width, below Zone 7, using the platform's existing `.gap-note`-style amber-tinted card as its visual basis (same background/border treatment already used for methodology callouts elsewhere), so it reads as "important context," consistent with how similar callouts already look on other pages.
- The button does not navigate to a different page — it manipulates Zone 5's expand-state and selection programmatically, then smooth-scrolls the user's viewport back up to Zone 5 so they see the newly-expanded, newly-selected row.

### B.6 — Business Context and Anomaly Detection pages: positional impact

**No layout changes to either page.** Both retain their exact current Zone structure (KPI strip, gauge, bullet/risk-strip, main trend chart, detail table) from the current build. The only change: both now display the same "Scoped to: X" caption described in B.4, and their existing calculations (historical banding, segment-level anomaly share) run against whatever node is scoped rather than always-global — a data-source change, not a visual one.

### B.7 — Executive Overview: positional impact

**One new card added, nothing removed or moved.** The existing RAG banner, 4-step storyline strip, 4 KPI cards, and summary text block all remain in their current order and position. A new, fifth element — the hierarchy-disagreement risk flag (Part A companion, Phase 11 of the original plan) — is inserted as a new card **between the RAG banner and the storyline strip**, styled identically to the RAG banner (same rounded-rectangle treatment, amber-toned) but visually smaller/secondary, so it reads as "here's a specific supporting risk" underneath the single overall verdict the RAG banner already gives, not a second competing headline.

---

## PART C — Cross-Component Data Flow Summary (how a click ripples through the page)

1. User clicks the "ANZ" row in the Zone 5 hierarchy table.
2. `currentScope = {level: 'SubRegion', node: 'ANZ'}` is set (a single shared JS object, not per-component state).
3. Zone 5's row gets the `selected` CSS class (teal-tinted background); the "Current Scope" pill in Zone 3 updates its label to "Scope: APJ > ANZ".
4. Zone 6's trend chart and evidence table re-render, filtered to ANZ's queue-week rows, title updates to reference ANZ.
5. Zone 7's tolerance-distribution chart recomputes its five buckets from ANZ's rows only.
6. Zone 8 (Root Cause panel) evaluates ANZ's classification/boundary-proximity; renders or stays hidden accordingly.
7. If the user then navigates to Model Champion (Zone 1 rail click), that page reads the same shared `currentScope` object on mount and immediately renders already-scoped to ANZ, with the "Scoped to: APJ > ANZ" caption visible before any further interaction.

This single shared `currentScope` object — read by every page, written only by the hierarchy table (and clearable via the Zone 3 pill's × control) — is the mechanism that makes cross-page persistence real rather than aspirational; it directly replaces the current build's per-page-only filter state.
