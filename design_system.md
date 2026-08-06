# Enterprise Forecast Decision Intelligence Platform: Design System

## Product Philosophy
The platform is an Enterprise Forecast Decision Intelligence Platform. It automates analytical reasoning that surfaces the business questions an experienced forecast analyst would ask — and answers them deterministically — before a human sees the report. It is NOT a chatbot, dashboard, report summarizer, LLM wrapper, or BI tool. It produces a Decision Support Document, not a recommendation engine. Core value: Observation is MORE important than Recommendation. Evidence is MORE important than Recommendation.

## Product Scope
Ingests backtest datasets containing actual volumes and model forecasts. Evaluates forecast accuracy across multiple ML models against an optional incumbent baseline. Produces a deterministic Decision Support Document answering four business questions. Supports Greenfield (no incumbent baseline) and Replacement (incumbent exists) scenarios.

## What the Product Is
An automated analytical investigation engine. A deterministic evidence-to-decision translation system. A forecast model evaluation and comparison platform. A policy-governed decision support system.

## What the Product Is Not
Not a forecasting engine (it evaluates forecasts, does not produce them). Not a recommendation engine (recommendations are conditionally permitted, not guaranteed). Not a causal inference system (it identifies associations, never causation). Not a financial impact calculator (impact stated only in volume units unless financial data is explicitly provided).

## Design Principles
1. Observation First: State exactly what happened before explaining why.
2. Evidence First: No observation exists without a deterministic metric supporting it.
3. Confidence Limitation: If evidence is weak, recommend nothing.
4. Explainability: Every metric must be mathematically reproducible.
5. Traceability: Every narrative claim maps to a typed evidence contract and a data source.
6. Conservative by Default: The system defaults to retaining the incumbent. Change requires positive evidence.
7. Deterministic Outputs: Given identical inputs and policy, the platform produces identical outputs.

## Report Philosophy
The report is a Decision Support Document, not an analytical report. Page 1 must stand alone — a VP reading only Page 1 must have enough information to approve or reject. The report is structured around business questions, not analytical modules. Every page answers exactly one business question. Information flows decision-first: What is the decision? What is the evidence? What is the confidence? What is the business impact?

## The Four Business Questions
1. Accuracy Assessment: Did human planners or ML produce more accurate forecasts?
2. Model Champion Selection: Which forecasting model ranked first across all evaluated candidates?
3. Business Context: Was the underlying demand volume stable enough to be forecasted?
4. Forecast Degradation: Did forecast error increase during periods of demand anomalies?

## Information Hierarchy
Every report section follows this hierarchy:
1. Business Question — The exact operational inquiry, phrased as a question.
2. Observation — Sterile factual statement of what occurred.
3. Primary Evidence — Maximum 3 metrics substantiating the observation.
4. Supporting Evidence — Maximum 5 metrics providing additional context.
5. Conclusion — One sentence, maximum 25 words, derived only from the evidence shown.
6. Decision Support — Why the conclusion matters operationally. Guidance only, never directives.
7. Recommendation — Present only when deterministic conditions are satisfied. Omitted otherwise.

## Observation Principles
Observations contain only numbers, comparators, and temporal references. No adjectives, adverbs, opinions, or interpretations. Observations state THAT something occurred, never WHY. Example of correct observation: "ML WAPE was 9.47%. Manual WAPE was 12.31%." Example of incorrect observation: "ML significantly outperformed the manual baseline."

## Evidence Principles
Primary Evidence: Maximum 3 metrics per question. These are the core proof. Supporting Evidence: Maximum 5 metrics per question. These provide diagnostic context. Evidence is strictly numerical. No narrative within evidence blocks. No conclusion may reference a metric not present in the evidence tables. Evidence cardinality limits are structural and non-negotiable.

## Conclusion Principles
Exactly one sentence per question. Maximum 25 words. Derivable solely from the evidence shown in the same section. States observations, never causation. If a conclusion requires more than 25 words, the business question is too broad.

## Decision Support Principles
Explains why a conclusion is operationally relevant. Never directs action. Never attributes causation. Uses guidance language: "should be considered when," "may be relevant to." Prohibited language: "therefore deploy," "must switch," "caused by."

## Recommendation Principles
Recommendations are deterministic: R = f(DecisionPolicy, Evidence, Confidence). If any input is missing, null, or below threshold: recommendation is suppressed (omitted entirely). Suppressed means omitted — not softened, hedged, replaced with "N/A", or replaced with "Suppressed". Recommendations are sourced verbatim from the Decision Intelligence layer. The Content layer never fabricates deployment directives. Questions 3 (Business Context) and 4 (Forecast Degradation) permanently prohibit recommendations. They provide context only. Questions 1 and 2 conditionally permit recommendations based on confidence level, evidence thresholds, and decision policy. The statistical winner is NOT automatically the operational recommendation. Ranking does not equal deployment.

## Confidence Philosophy
Confidence is mathematically derived, never hardcoded or inferred. Confidence is always derived from named analytical inputs (p-value, win rate, sample size, effect size). Three tiers: HIGH (actionable immediately), MEDIUM (actionable with human review), LOW (no operational change permitted). Statistical significance (p-value) alone is insufficient. Practical significance (effect size) is required alongside. Sample size below minimum forces confidence to LOW regardless of other metrics.

## Dynamic Report Composition
Reports dynamically expand or contract based on available evidence. Sections are never fully removed. They always appear, even if condensed. Condensation rules: Manual baseline missing (Greenfield): Condense Accuracy Assessment to single statement. Single model scored: Condense Model Champion Selection to single statement. Zero anomalies detected: Condense Forecast Degradation to single statement. Confidence unavailable: Suppress ALL recommendations across all sections. Sample size below minimum: Suppress ALL recommendations; add data sufficiency warning. Condensed = minimal single-observation format. Suppressed = block omitted entirely.

## Anti-Patterns
1. Causal Language: Permanently banned phrases — "caused by", "due to", "because of", "driven by", "attributable to", "as a result of", "proves that", "demonstrates that" (when implying causation). Permitted alternatives: "observed during", "co-occurred with", "coincided with", "was associated with", "should be considered when".
2. Financial Hallucination: System must never state financial impact (revenue, margin, cost) unless explicit financial data is provided in the input. Impact must be stated only in the units the system has access to (e.g., volume units).
3. Recommendation Inflation: Softening a suppressed recommendation ("Consider exploring...") instead of omitting it entirely.
4. Evidence-Free Conclusions: Any conclusion referencing metrics not present in the section's evidence tables.
5. Observation Editorializing: Adding adjectives, opinions, or qualitative assessments to observations.
6. Confidence Fabrication: Assigning confidence levels without deriving them from statistical tests.
7. Causal Root Cause Claims: Claiming to know WHY a forecast failed without external causal data. The system can only identify WHAT happened and WHEN.

## Immutable Design Rules
1. Observation is more important than Recommendation.
2. Evidence is more important than Recommendation.
3. If evidence is weak, recommend nothing.
4. Statistical winner does not equal operational recommendation.
5. The system never claims causation.
6. Confidence is derived, never assigned.
7. Financial impact is stated only in available data units.
8. Every claim traces to a typed evidence source.
9. Page 1 stands alone as a complete decision artifact.
10. Sections condense but never disappear.
11. Recommendations are omitted when suppressed, never softened.
12. Primary evidence maximum 3 metrics. Supporting evidence maximum 5 metrics.
13. Conclusions are exactly one sentence, maximum 25 words.
14. Questions 3 and 4 never produce recommendations.
