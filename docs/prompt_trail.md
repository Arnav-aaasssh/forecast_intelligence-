# Enterprise Forecast Decision Intelligence Platform: Prompt Trail & Evolution

## Initial Product Thinking
The platform began as a review pipeline — a system that computed statistical metrics and formatted them into a report. Initial architecture was a monolithic scorer that performed all computation, decision-making, and report generation in a single module. The system behaved like a data scientist's notebook: compute metrics, format tables, output Markdown. The fundamental gap identified: the system was architected as a review tool, not a decision intelligence platform. This gap was architectural, not a defect. Core realization: a statistical calculator is not the same as a decision support system. The business needed analytical reasoning, not formatted averages.

## Report Evolution
Phase 1 (8-page analyst report): Structured by analytical modules. Separate Macro and Micro pages for each question. Designed for analysts, not executives. Self-critique: Too long for a 10-minute executive read. Page 1 did not stand alone. Splitting Q1/Q2 into Macro/Micro destroyed narrative coherence.

Phase 2 (6-page executive report): Consolidated Macro/Micro into unified pages. Reordered to follow a McKinsey strategy deck narrative (Action → Reality → Strategy → Tactic → Risk → Proof). Key insight: Actuals (business volume) should come BEFORE accuracy assessment because you cannot explain forecast accuracy without first establishing volume reality. Self-critique: This executive ordering works for strategy decks but not for weekly diagnostic use by planning managers.

Phase 3 (Planning Manager diagnostic flow): Reordered for operational diagnostics (Score → Why did we miss? → Did volume break it? → How to fix it?). Key insight: Different audiences need different information ordering. A planner asks "What was our score?" first. An executive asks "What should I approve?" first. Resolution: The platform adopted the Planner flow for body sections but preserved the Executive Dashboard as Page 1.

Phase 4 (Dynamic composition): Introduced disappearing/condensing pages. Sections that lack sufficient data condense to single statements instead of rendering empty pages with null values. Key insight: An executive loses trust instantly upon seeing empty pages full of null values. Dynamic condensation maintains credibility.

## Architecture Evolution
Phase 1 (Monolith): Single module performing scoring, comparison, recommendation, and report generation.

Phase 2 (Modular decomposition): Decomposed into domain-driven analytical modules aligned with business questions (actuals.py, performance.py, comparison.py, degradation.py, recommendation.py). Decision: Domain-driven module organization was chosen over mathematical-function-based organization. Domain alignment means changing how Manual vs ML comparison works touches only one file. Rejected alternative: Mathematically-grouped flat modules were initially proposed but violated business cohesion.

Phase 3 (Layer separation): Introduced the 3-layer architecture (Analytics → Decision Intelligence → Presentation). This was later refined to 6 layers by splitting Data Validation, Content Engine, and PDF Rendering into distinct layers. Rejected: Over-engineered alternatives including hypothesis testing pipelines, state evaluation engines, and multi-stage orchestration abstractions. These were deemed unnecessary for a 13-week dataset. Rejected: Complete architectural flattening into god-scripts. Proper modularity was necessary even for MVP.

Phase 4 (Contract-driven architecture): Replaced dictionary-based communication with strongly-typed frozen dataclasses. Introduced contract narrowing between layers. Key insight: Weakly-typed interfaces create hidden dependencies. A dictionary key typo produces silent failure. Strongly-typed contracts produce immediate, traceable errors.

Phase 5 (Immutable contracts): Applied frozen=True to all dataclasses. No downstream layer can mutate upstream evidence.

## Decision Intelligence Introduction
The original system conflated three concepts: statistical winner, operational recommendation, and deployment decision. Architectural separation recognized that these are three distinct concerns: Which model scored highest? (Analytics layer — mathematical fact.) Should we deploy it? (Decision Intelligence — policy application.) How should we deploy it? (Decision Intelligence — scenario evaluation.) This separation was the single most important architectural insight. A model winning statistically does not justify deployment if confidence is low, improvement is marginal, or switching costs exceed benefit. The DecisionPolicy was introduced to externalize all business thresholds. Previously, thresholds were hardcoded across 30+ locations in 6+ files. The Executive Decision Matrix was introduced to map (Confidence × Impact × Complexity) to deterministic actions. Progressive complexity escalation was adopted: system defaults to Global deployment. Regional requires >1% improvement. Segmented requires >2% improvement. Complexity must be earned.

## Content Engine Evolution
Phase 1 (Report builder): Content was generated inline within the report rendering module. Analytics, narrative, and formatting were interleaved.

Phase 2 (Separated builders): Content generation was extracted into dedicated builder functions, each answering one business question. Key decision: Builders were made pure functions that do not import pandas, numpy, or scipy. This prevents mathematical computation from leaking into the content layer.

Phase 3 (Structural contracts): Builders began returning structured ReportSection objects instead of Markdown strings. This decoupled content from presentation format.

Phase 4 (8-field content architecture): The legacy content hierarchy was permanently deprecated. Replaced with a deterministic 8-field contract (Business Question, Observation, Primary Evidence, Supporting Evidence, Conclusion, Decision Support, Recommendation, Recommendation Suppression).

Phase 5 (Traceability): TraceabilityMetadata added to every section, recording source layer and originating contract types.

Phase 6 (Immutable ContentContract): ReportDocument replaced with frozen ContentContract. The document structure itself became an immutable typed contract.

## Evidence-First Philosophy
The platform's relationship with evidence evolved through three stages:
1. Evidence as decoration: Metrics were computed and placed in tables to support predetermined narratives.
2. Evidence as structure: Metrics became the primary content, with narrative serving to explain them.
3. Evidence as authority: No narrative statement may exist without a corresponding metric in the evidence tables. Evidence cardinality limits were imposed (Primary ≤ 3, Supporting ≤ 5) to force prioritization.

The principle "Observation is more important than Recommendation; Evidence is more important than Recommendation" became the platform's foundational design axiom.

## Recommendation Philosophy
Phase 1 (Always recommend): Every section produced a recommendation, even when evidence was weak. This created trust problems when low-confidence recommendations contradicted executive judgment.

Phase 2 (Soften when uncertain): Weak recommendations were hedged with language like "Consider exploring..." or replaced with "N/A". This was worse — it appeared evasive.

Phase 3 (Suppress when uncertain): Recommendations became deterministic functions: R = f(Policy, Evidence, Confidence). Missing input = complete omission. No softening, no hedging, no "N/A".

Phase 4 (Permanent prohibition): Questions 3 (Business Context) and 4 (Forecast Degradation) were permanently prohibited from producing recommendations. These sections exist solely to provide interpretive context.

Key principle adopted: The content layer never fabricates recommendations. Recommendations are sourced from the Decision Intelligence layer or omitted entirely.

## Dynamic Report Composition
Initially, the report had a fixed structure. Every section always rendered, even when data was insufficient. Problem identified: Greenfield scenarios (no manual baseline) produced sections full of "null", "N/A", and 0.0% — destroying executive trust. Solution: Dynamic condensation. Sections with insufficient data condense to single-statement summaries. Sections are never fully removed — they always appear in the report to maintain structural consistency. This philosophy extended to: single-model scenarios (Q2 condenses), zero-anomaly scenarios (Q4 condenses), and insufficient sample size (all recommendations suppressed).

## Final Analytical Philosophy
All computation is deterministic. No LLM inference in the analytical pipeline. Statistical significance (p-value) alone is insufficient for decision-making. Practical significance (effect size) is required. Sample size below minimum forces LOW confidence regardless of other metrics. The system aggregates to weekly temporal grain before statistical testing. Executing tests on daily rows artificially inflates N and produces false-positive significance. Seasonality analysis on 13 weeks of data is a statistical fallacy. Permanently rejected. The system identifies associations, never causation. Without external causal data, claiming root cause is hallucination.

## Final Decision Support Philosophy
The platform produces a Decision Support Document, not a decision. The system provides evidence, observations, and guidance. The executive makes the decision. Recommendations are permitted only when mathematically justified by the policy engine. When permitted, recommendations identify the statistical champion and deployment scenario. They do not mandate operational change. The system is conservative by default. Retaining the incumbent is the default action. Switching requires positive evidence meeting defined thresholds.

## Permanent Lessons Learned
1. A statistical calculator is not a decision support system. The gap is architectural.
2. Over-engineering kills clarity. Simple, deterministic modules aligned to business questions are superior to abstract frameworks.
3. The system can only say WHAT happened, not WHY. Claiming causation without causal data destroys trust.
4. Financial hallucination is an existential risk. Never state financial impact without financial data.
5. Weak evidence demands silence, not hedging. Omit, do not soften.
6. Reports structured around business questions outperform reports structured around code modules.
7. Different audiences need different information ordering — but Page 1 must always stand alone.
8. Protect validated assets. Deprecate, never delete. Parity before migration.
9. Immutable contracts prevent an entire class of integration defects.
10. Thresholds externalized into policy objects enable business stakeholders to modify system behavior without engineering changes.
