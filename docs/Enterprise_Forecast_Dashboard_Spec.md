# Design Specification: Enterprise Forecast Decision Intelligence Dashboard

## 1. Executive Summary
This specification defines a static, point-in-time dashboard that replaces the platform's Markdown Decision Support Document with an interactive visual interface, without changing what the platform is: a deterministic, evidence-first system that answers four fixed business questions about forecast accuracy, model selection, demand stability, and anomaly behavior. The dashboard's job is not to look impressive — it is to let three distinct users (executive, forecast analyst, model owner) each get to their own decision-relevant answer in under 30 seconds, with every number traceable to a policy and a computation, and every recommendation visually distinguished from an unsupported observation.

The design principle governing every choice below: **confidence is a first-class visual citizen, not a footnote.** Nothing in this dashboard should ever imply certainty the underlying statistics don't support.

## 2. Design Objectives
**Primary objective:** Let a user answer "what should we do, and how sure are we?" for contact-center forecasting decisions, faster and with more confidence than the static report allowed.

**Secondary objectives:**
* Make the full 92-model leaderboard genuinely explorable (the report only showed top 10).
* Make policy thresholds and known engine limitations visible in-context, not buried in an appendix.
* Preserve the platform's non-negotiables: no causal language, no fabricated confidence, suppressed recommendations stay suppressed, Page 1 (Executive view) must stand alone.

**Success criteria:**
* A VP can state the operational decision and its confidence level without scrolling, within 10 seconds of opening the dashboard.
* A forecast analyst can locate any specific model's full metric breakdown in under 3 interactions.
* No user can mistake a Low-confidence finding for a recommendation, even glancing quickly.

**Key business questions the dashboard answers** (unchanged from the platform's frozen architecture):
* Did Manual or ML forecasting perform better?
* Which model ranked first, and how much should that be trusted?
* Was demand stable enough to forecast reliably?
* Did forecast accuracy degrade during demand anomalies?

## 3. Target Users
**Primary users:**
* **Executive / VP of Operations:** Glances at the dashboard before a planning meeting; needs the decision and its confidence, nothing else, unless they choose to dig further.
* **Forecast Analyst / Planning Manager:** Uses the dashboard weekly to check whether the current model recommendation still holds, investigate specific segments, and prepare talking points for stakeholders.

**Secondary users:**
* **Data Scientist / Model Owner:** Audits the scoring methodology, checks why a specific model ranked where it did, verifies policy bounds are being applied correctly.
* **Compliance / Audit reviewer:** Occasionally needs to trace a displayed number back to its formula and policy version.

**User goals:**
* **Executive:** Confirm or challenge a recommendation in one glance.
* **Analyst:** Understand why a number is what it is, and whether it's actionable.
* **Data scientist:** Verify correctness and completeness of the scoring logic.

**Daily/weekly workflow:**
Open dashboard → check Executive Overview → if decision is unchanged and confidence is stable, close it (10 seconds). If something changed (confidence dropped, new champion, new anomaly), drill into the relevant question tab, check the leaderboard/detail table, decide whether to escalate.

**Pain points this design must solve:**
* Static reports bury the "how sure are we" signal inside prose (a *p = 0.53* in a sentence is easy to miss).
* Long documents make daily re-checking expensive.
* Top-10-only leaderboards hide models the analyst actually cares about.
* Suppressed recommendations, if not visually distinct, look like the system just forgot to write one.

**Information needed most frequently:**
Current operational decision, its confidence tier, and whether anything changed since last check.

## 4. Information Architecture
* **Tier 1 — Always visible, no interaction required (Executive Overview):** Operational decision, its confidence, the champion model's headline score, and volume stability status. This is the entire Page-1-stands-alone requirement made literal: four facts, zero scrolling.
* **Tier 2 — One click away (Question tabs Q1–Q4):** Each question's Observation → Primary Evidence → Supporting Evidence → Conclusion → Decision Support → Recommendation (or its explicit omission). This is where an analyst's normal workflow lives.
* **Tier 3 — Two clicks away (leaderboard, per-model detail, policy snapshot):** Full 92-model sortable/searchable table, family-level comparison, and the underlying policy bounds/weights. This is progressive disclosure for the data scientist / auditor persona — present, but not competing for attention with Tier 1/2.
* **Optional / on-demand information:** Known policy gaps and limitations (e.g., no segment-coverage floor), full statistical test parameters, traceability metadata. These are collapsed by default and expand on request — they matter for trust but would clutter a daily-use view if always open.

**Rationale for this hierarchy:**
The same underlying evidence serves three very different attention budgets (10 seconds / 2 minutes / 15 minutes). Rather than three separate documents, one information space with disclosure depth matching user intent avoids duplicating logic while respecting all three.

## 5. Dashboard Layout Plan
* **Overall page structure:** A fixed header (identity + decision status, always visible even while scrolling), a horizontal tab strip immediately below it (Executive / Q1 / Q2 / Q3 / Q4), and a single-column-of-sections content area beneath. No sidebar — a persistent sidebar would compete for the same "always visible" real estate the header status already owns, and this dashboard has five destinations, not fifty; a tab strip is sufficient and lower-overhead than a collapsible sidebar.
* **Header:** Two zones. Left: platform name, dashboard title, evaluation period. Right: generation timestamp, dataset size, models-evaluated count — the provenance facts an auditor checks first and everyone else ignores, so they're present but visually quiet (smaller, muted).
* **Navigation:** Horizontal tabs, not a sidebar, not a dropdown — five destinations are within comfortable eye-scan range and tabs communicate "these are five views of one dataset," which is the correct mental model (versus a sidebar's implication of a deeper, branching hierarchy this dashboard doesn't have).

**Main content per tab, general pattern:**
* A KPI row at the top (3–4 cards): the numbers this tab exists to answer, nothing else, sized for a 3-second read.
* Below that, a two-column split: a chart (left, larger) paired with the evidence/observation/conclusion block (right) — chart and narrative side by side so the user never has to reconcile "which number does this line represent" across a scroll gap.
* Where a table is the primary content (Q2's leaderboard), it takes the full width beneath the charts, since tables need horizontal room to breathe.

* **Cards:** Used for two distinct purposes that should look distinct — KPI cards (compact, numeric, glanceable) versus evidence cards (taller, containing the Observation/Evidence/Conclusion narrative block). Do not let these visually blend into one undifferentiated "card soup"; KPI cards are terminal (nothing to click), evidence cards contain read content.
* **Filters:** None globally — this is a static snapshot of one evaluation run, not a live multi-period explorer, so a global date/region filter bar would imply capability that doesn't exist. The only interactive filtering lives locally inside the leaderboard (model name search, column sort), scoped to where it's actually useful.
* **Action panels:** Minimal by design intent — this is a decision support document, not a workflow tool. The one "action" surface is the recommendation block itself, and it should never contain a button; it states guidance, per the platform's prohibition on the system directing action.
* **Detail views:** Clicking a model row in the leaderboard should reveal (inline expansion, not a navigation-away modal) that model's full metric breakdown and its score-contribution decomposition — keeping the user in place rather than losing their scroll position and leaderboard sort state.

## 6. User Experience

### Executive Overview
* **Objective:** Confirm the decision hasn't changed and doesn't need escalation.
* **Interaction:** Passive read, zero clicks expected.
* **Navigation flow:** This is the landing tab; user may never leave it on a typical day.
* **Ease of use:** Success = user can restate the decision and its confidence without re-reading, from memory, seconds after closing the tab.

### Q1 (Strategy Assessment) / Q3 (Business Context) / Q4 (Anomaly Behaviour)
* **Objective:** Verify or investigate a specific claim.
* **Interaction:** Read evidence table, hover chart for exact values at a point in time.
* **Navigation flow:** Single tab, no further drill-down needed — these questions resolve to one conclusion each.
* **Ease of use:** The evidence-to-conclusion chain must be readable top-to-bottom without needing to cross-reference another tab.

### Q2 (Model Champion)
* **Objective:** Identify current champion, understand why, check if a specific model of interest ranks well.
* **Interaction:** Active — search leaderboard, sort by column, expand a row for detail.
* **Navigation flow:** KPI/chart summary first, then descend into the table; this is the one tab where users are expected to spend real time.
* **Ease of use:** Search must filter instantly (client-side, no loading state); sort must indicate current sort column/direction unambiguously.

### Accessibility considerations (all tabs):
* Confidence must never be color-only — always pair the color chip with the text label ("High"/"Medium"/"Low"), since color-blind users and grayscale printing must retain full meaning.
* All chart data must have an equivalent tabular representation available (the evidence tables already provide this by design — charts illustrate, tables are the source of truth).
* Sufficient contrast between chip backgrounds and text (verify against WCAG AA at minimum, given this is a professional/compliance-adjacent tool).
* Keyboard navigability for tab switching and table sorting (no interaction should be mouse-only).

### Responsive design strategy:
This is fundamentally a desktop/large-monitor tool (used during planning meetings, side-by-side with spreadsheets) — mobile is a secondary concern, not primary. At minimum: KPI cards should reflow from a 4-column to 2-column grid below ~900px, the two-column chart/evidence split should stack vertically below the same breakpoint, and the leaderboard should permit horizontal scroll rather than attempting to compress 8 columns onto a phone screen. Do not invest disproportionate effort in a phone-first leaderboard experience — the persona doesn't ask for it.

## 7. Visual Design Guidelines
* **Design language:** Institutional-analytical, not consumer-SaaS. This tool sits closer to a financial audit report or a scientific dashboard than a marketing analytics product — the visual language should communicate rigor and restraint, not energy or excitement.
* **Visual hierarchy:** Three tiers, strictly separated by size and weight: (1) the operational decision — largest, boldest element on the page; (2) KPI numbers — second-largest, but clearly subordinate; (3) supporting evidence/body text — smallest, quietest. No element should compete with the decision statement for attention on the Executive tab.
* **Typography:** A distinct display face for headlines and large numbers (giving the "reviewed document" feel, not a generic dashboard font), paired with a clean, highly legible sans-serif for body/table content, and a monospace face reserved specifically for data labels, statistical values (p-values, scores), and confidence chips — using monospace consistently for anything numeric-and-precise helps the eye distinguish "this is a measured value" from "this is prose" at a glance.
* **Color philosophy:** Color is semantic, not decorative. One neutral "institutional" color (a deep navy or slate) anchors the brand/header and all default UI chrome. One accent color represents "good/confirmed/positive" and is used sparingly — for the High-confidence chip and for the better side of any Manual-vs-ML comparison. A second, distinct accent represents caution/Medium-confidence. A muted neutral (not a color at all, deliberately desaturated) represents Low-confidence — the visual instinct should be "this is quieter, not more special," reinforcing that low confidence means do-not-act. A warning color (not the same as either confidence color) is reserved exclusively for anomalies and negative/regression findings, so it's never ambiguous whether a red-ish mark means "risk" or "medium-confidence."
* **Spacing:** Generous whitespace between the KPI row and the chart/evidence row — these are different types of information and should not visually run together. Within a table, tighter, consistent row spacing to maximize scannable density, since the leaderboard persona (analyst) explicitly wants information density there.
* **Card design:** Flat or near-flat (minimal shadow), thin single-pixel borders rather than heavy drop shadows — heavy shadows read as consumer-app styling and undercut the institutional tone. Consistent corner radius, small (not the rounded-pill aesthetic of consumer dashboards).
* **Icons:** Used sparingly and only where they remove ambiguity (e.g., a small info icon that reveals traceability metadata on hover/click) — not decoratively on every KPI card. An icon on every card is a common templated default and should be avoided; most KPI cards need no icon at all.
* **White space usage:** White space is the primary tool for signaling "this section is done, a new section begins" — rely on spacing and subtle background shifts over heavy dividing lines.
* **Contrast & emphasis strategy:** The confidence chip and the operational decision text are the only two elements on the entire dashboard permitted "loud" visual treatment (bold color fill, larger scale). Everything else — including chart lines, evidence numbers, table content — stays in a restrained, professional register so the two things that matter most are never competing with decoration for the eye's attention.

## 8. UI Component Inventory

| Component | Purpose | Priority | Placement | Interaction |
| :--- | :--- | :--- | :--- | :--- |
| **Header bar** | Identity, provenance, timestamp | Must-have | Fixed top | Static, no interaction |
| **Tab navigation** | Switch between 5 views | Must-have | Below header | Click/keyboard select |
| **KPI card** | Single headline metric | Must-have | Top of each tab | Static (hover for exact value optional) |
| **Confidence chip** | Visual + textual confidence tier | Must-have (signature element) | Wherever a claim/recommendation appears | Static, possibly hover for methodology tooltip |
| **Evidence card** | Observation/Evidence/Conclusion/Decision Support block | Must-have | Paired beside charts on Q1/Q3/Q4, below charts on Q2 | Static read |
| **Recommendation block** | Guidance text, or explicit "omitted" state | Must-have | Bottom of evidence card | Static; visually distinct styling when suppressed vs. active |
| **Trend/line chart** | Time-series (WAPE, volume) | Must-have | Q1, Q3, Q4 primary chart area | Hover for point values |
| **Bar/comparison chart** | Champion vs runner-up, family comparison | Must-have | Q2 | Hover for value, possibly click-to-highlight |
| **Sortable/searchable leaderboard table** | Full model comparison | Must-have | Q2, full width | Click column header to sort, type to search, click row to expand |
| **Expandable row detail** | Per-model score decomposition | Should-have | Within leaderboard | Click to expand/collapse in place |
| **Policy/traceability disclosure** | Reveal underlying formula/policy bound for a number | Should-have | Small (i) affordance near key metrics | Click or hover to reveal, collapsed by default |
| **Known-gap notice** | Surface documented engine limitations | Should-have | Contextually near the affected finding (e.g., Q2) | Static, visually distinct (muted warning tone), always visible where relevant — not hidden behind a click, since this is a trust/integrity disclosure |
| **Footer** | Methodology/version statement | Nice-to-have | Bottom of page | Static |

## 9. Interaction Guidelines
* **Tab switches should be instantaneous** (no loading spinner) since this is a static, pre-computed snapshot — any perceptible delay would misrepresent the nature of the tool.
* **Table sorting and search must update the visible rows immediately** on interaction, with the current sort column/direction always visibly indicated (never leave the user guessing which column is driving the current order).
* **Hover states on charts should reveal exact values**, since the chart's job is pattern-recognition and the table/evidence block's job is precision — hover is the bridge between them.
* **Expandable elements** (row detail, gap disclosures) should use a consistent, predictable expand/collapse affordance throughout the dashboard — one interaction pattern, not several competing ones.
* **Nothing on this dashboard should imply a write action** (no buttons that suggest "approve," "deploy," "switch model") — this is a decision support artifact; the human is the actor, not the interface.

## 10. Accessibility Considerations
* Confidence and status information must be conveyed through text + shape/pattern in addition to color (addressed in Section 6, restated here as a hard requirement, not a suggestion).
* Minimum WCAG AA contrast ratios for all text, especially inside colored chips where background/text pairings are most at risk of failing contrast checks.
* All interactive elements (tabs, sortable headers, expandable rows) must be reachable and operable via keyboard alone.
* Chart data must not be the sole source of any fact — every charted value must also exist in an adjacent table or evidence list, both for accessibility and for the platform's own "evidence over visualization" principle.

## 11. Responsive Design Strategy
* **Breakpoint philosophy:** Design desktop-first (primary use context is a planning meeting or an analyst's monitor), with a single meaningful breakpoint around tablet width where density reduces gracefully (4-column KPI rows → 2-column; side-by-side chart/evidence → stacked).
* **Leaderboard on small screens:** Permit horizontal scroll rather than compressing or hiding columns — hiding data columns on a data-integrity tool is worse than requiring a scroll gesture.
* **Do not design a fundamentally different mobile experience** or navigation pattern; the same tab structure and information hierarchy should hold at every size, only density and column layout should adapt.

## 12. Design Justification
* **Why tabs over a sidebar:** Five flat, non-hierarchical destinations map naturally to horizontal tabs; a sidebar would suggest a deeper navigation tree that doesn't exist here and would consume permanent horizontal space this content-dense dashboard needs for tables and charts.
* **Why the confidence chip is the one "signature" design element:** The platform's entire reason for existing is to prevent statistical overconfidence from reaching decision-makers unfiltered. A dashboard that treats "High confidence" and "Low confidence" findings with identical visual weight would actively undermine the platform's core value proposition. Making confidence maximally, consistently visible is not a stylistic flourish — it is the single highest-leverage design decision available, because it's the one piece of information most likely to be skimmed past in a text report and most dangerous to miss.
* **Why progressive disclosure over a single dense page:** The three personas have genuinely different time budgets (seconds / minutes / potentially 15+ minutes for an auditor). A single page trying to serve all three simultaneously would either overwhelm the executive or under-serve the analyst. Tiered disclosure (Executive glance → Question tabs → Leaderboard/detail) lets the same underlying evidence base serve all three without three separate documents to keep in sync.
* **Why restraint over visual excitement:** This tool's credibility depends on reading as rigorous and trustworthy, not exciting. Over-designed dashboards (heavy shadows, playful color, dense iconography) read as marketing artifacts, which is precisely the wrong register for a document whose stated purpose is to prevent the platform from ever sounding more certain than the statistics support.
* **Trade-off acknowledged:** This design intentionally sacrifices some "wow factor" and visual density-as-spectacle in favor of scan-speed and trust signaling. For this specific audience (executives and forecast analysts making real operational decisions), that trade-off is correct; it would be the wrong trade-off for a public-facing marketing dashboard, which is not what this is.

## 13. Implementation Priorities

**Must-have (v1, blocks release):**
1. Header + tab navigation shell
2. Executive Overview tab (KPI row + primary chart + evidence card)
3. Q1/Q3/Q4 tabs (KPI row + chart + evidence card each)
4. Q2 tab with full sortable/searchable 92-model leaderboard
5. Confidence chip component, used consistently everywhere a claim appears
6. Explicit suppressed-recommendation visual state (distinct from an active recommendation)

**Should-have (v1.1):**
7. Expandable leaderboard row detail (score decomposition per model)
8. Known-policy-gap disclosure boxes
9. Traceability/methodology hover disclosures on key metrics

**Nice-to-have (future):**
10. Print/PDF-optimized stylesheet
11. Comparative view against the legacy service's parallel JSON output (risk/drift scores), if that data source is formally adopted as a second input

---
*This specification is implementation-ready: an engineering team or coding model can build directly from Sections 4–9 and 13 without further design decisions, referring back to Sections 2, 10, and 12 whenever a judgment call arises during build.*
