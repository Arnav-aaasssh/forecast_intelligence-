# Enterprise Forecast Decision Intelligence Platform: Technical Architecture

## Product Goal
Transform raw backtest data into a deterministic Decision Support Document through a strictly layered, contract-driven pipeline. Each layer performs exactly one category of work. No layer performs work belonging to another layer.

## System Layers
The platform operates as a 6-layer sequential pipeline:
1. Data Validation Layer
2. Analytics Layer
3. Decision Intelligence Layer
4. Content Engine Layer
5. Markdown Renderer Layer
6. PDF Renderer Layer

## Layer Responsibilities

### Data Validation Layer
Ingests the backtest dataset. Validates required schema columns (ML_Forecast, Actual_Offered, Model, Family, Week_Ending). Drops rows with missing actuals. Enriches dataset with computed error fields. Instantiates configuration objects (ScorerConfig, DecisionPolicy). Halts pipeline if validation fails.

### Analytics Layer
Executes all deterministic mathematical computation. Produces typed evidence contracts: ActualsAnalysis, PerformanceEvidence, RecommendationEvidence, DegradationEvidence. Operates on DataFrames as input, returns strongly-typed dataclass objects as output. Contains all statistical tests (Wilcoxon signed-rank), normalization (Winsorized Min-Max), and scoring algorithms. Does not import or reference any decision policy, content generation, or presentation logic.

### Decision Intelligence Layer
Applies business policy to analytical evidence. Consumes: RecommendationEvidence, segment winners, DecisionPolicy. Produces: ExecutiveDecision (action, business impact, deployment scenario, reasoning). Implements a deterministic decision matrix: Evaluates three deployment scenarios (Global, Regional, Segmented) with blended WAPE. Classifies business impact (High, Medium, Low) based on improvement thresholds. Scores deployment complexity (Low = 1 model, Medium = 2-4, High = 5+). Maps (Confidence × Impact × Complexity) to action: Retain Incumbent, Pilot Deployment, Full Switch. Conservative by default: defaults to Global deployment; complexity must be earned by accuracy improvement exceeding policy thresholds (>1% for Regional, >2% for Segmented). Every decision carries a human-readable reasoning field. Does not perform any statistical calculation.

### Content Engine Layer
Pure translation layer: transforms evidence contracts into linguistic narratives. Consumes: narrow projection contracts (AnalyticsContract, DecisionContract, Q1Contract) and raw evidence objects. Produces: ReportSection objects assembled into a ContentContract. Each builder answers exactly one business question. Builders are pure functions: no imports of pandas, numpy, scipy. Cannot perform math. Builders emit structural objects (ChartDescriptor, ReportTable), not formatted strings. Enforces recommendation suppression deterministically via boolean flag. Carries TraceabilityMetadata on every section.

### Markdown Renderer Layer
Transforms ContentContract into a Markdown file. Format-agnostic to content semantics — does not know what Q1 or Q4 mean. Renders sections sequentially in fixed order. Respects section flags: is_condensed for compact rendering, recommendation_suppressed for omission. Single responsibility: formatting only.

### PDF Renderer Layer
Transforms Markdown into a styled PDF document. Owns typography, CSS styling, page breaks, and pagination. Zero content awareness.

## Layer Boundaries
Each layer is BANNED from performing work belonging to other layers:

- Data Validation: Banned from Statistical calculation, business logic, narrative generation, rendering
- Analytics: Banned from Policy application, narrative generation, rendering, data loading
- Decision Intelligence: Banned from Statistical calculation, narrative generation, rendering
- Content Engine: Banned from Statistical calculation, policy evaluation, rendering
- Markdown Renderer: Banned from Statistical calculation, policy evaluation, content generation
- PDF Renderer: Banned from Everything except typography and pagination

## Layer Contracts
All inter-layer communication occurs via strongly-typed frozen dataclass objects. No layer communicates via dictionaries, untyped arrays, or raw strings. No layer communicates backwards (upstream). Contracts are immutable (frozen=True). No downstream layer may mutate an upstream contract.

### Contract Narrowing Principle
Between the Decision Intelligence layer and the Content Engine, full evidence objects are projected into slim, purpose-built contracts:
- AnalyticsContract: Exposes only overall_confidence, baseline_wape, challenger_wape.
- DecisionContract: Exposes only action, deployment_scenario_name, is_greenfield.
- Q1Contract: Exposes only has_baseline, manual_wape, ml_wape, ml_won, confidence_level, action_recommendation.

This enforces information hiding: the content layer cannot access or be influenced by evidence it is not authorized to see.

## Responsibility Matrix
- Data Loading & Schema Validation: Data Validation (Orchestrator)
- Pipeline Sequencing: Data Validation (Orchestrator)
- WAPE, Bias, Hit10 Calculation: Analytics
- Composite Scoring & Normalization: Analytics
- Wilcoxon Signed-Rank Test: Analytics
- Anomaly Detection (Z-Score): Analytics
- Degradation Association: Analytics
- Confidence Classification: Analytics
- Policy Threshold Application: Decision Intelligence
- Deployment Scenario Selection: Decision Intelligence
- Business Impact Classification: Decision Intelligence
- Final Action Decision: Decision Intelligence
- Executive Dashboard Narrative: Content Engine
- Q1-Q4 Section Narratives: Content Engine
- Appendix Audit Tables: Content Engine
- Chart Descriptor Emission: Content Engine
- Markdown Formatting: Markdown Renderer
- Section Ordering: Markdown Renderer
- Table Rendering (GFM): Markdown Renderer
- Typography & CSS: PDF Renderer
- Page Breaks & Pagination: PDF Renderer

## Data Flow
The pipeline transforms data through progressive refinement:
1. Raw Excel → Validated DataFrame (Data Validation)
2. DataFrame → Evidence Objects (Analytics)
3. Evidence + Policy → Executive Decision (Decision Intelligence)
4. Decision + Evidence → Narrow Contracts → Report Sections → Content Contract (Content Engine)
5. Content Contract → Markdown File (Renderer)
6. Markdown → PDF (Renderer)

## Evidence Flow
Evidence objects are the currency of analytical truth. ActualsAnalysis flows to Q3 Builder and Appendix Builder. PerformanceEvidence flows to Q2 Builder and Appendix Builder. RecommendationEvidence flows to Q2 Builder, Executive Builder, and Appendix Builder. DegradationEvidence flows to Q4 Builder. ComparisonEvidence and StatisticalEvidence are embedded within RecommendationEvidence. Evidence objects are consumed by the Decision Intelligence layer and by the Content Engine, but never modified by either.

## Decision Flow
DecisionPolicy is instantiated once by the orchestrator. DecisionPolicy is injected into the Decision Intelligence layer. The Decision Intelligence layer produces a single ExecutiveDecision object. ExecutiveDecision is projected into DecisionContract for the Content Engine. The Content Engine never sees or references DecisionPolicy directly.

## Content Flow
Each builder receives narrow contracts or evidence objects. Each builder returns a single ReportSection. All ReportSections are assembled into a single ContentContract. The ContentContract is the sole input to the Markdown Renderer. The ContentContract is a complete, self-contained document description.

## Traceability Model
Every ReportSection carries a TraceabilityMetadata object. TraceabilityMetadata records: source_layer (always "Content Engine") and originating_contract_types (list of upstream contract names that produced the section). This enables audit: given any report section, the system can identify which evidence contracts were consumed to produce it. Full chain: Data Source → Evidence Object → Decision Object → Narrow Contract → Report Section → Rendered Output.

## Validation Philosophy
Ground truth parity is the ultimate acceptance criterion. All metrics validated to ±1e-5 floating-point tolerance. Two consecutive runs must produce identical outputs. Independent validation scripts compute metrics from raw data and compare against engine outputs. Parity must be demonstrated BEFORE deprecating any legacy component.

## Deterministic Design Philosophy
Given identical input data and identical policy configuration, the platform produces byte-identical output. No randomness, no LLM inference, no probabilistic decisions in the pipeline. All thresholds are externalized in configuration objects, not embedded in logic. Mathematical facts (WAPE, Bias, Wilcoxon) are immutable algorithms. Business policies (confidence thresholds, improvement minimums) are configurable parameters. The separation of mathematical fact from business policy is a foundational architectural principle.

## Policy Configuration Philosophy
Two configuration objects govern all tunable behavior: ScorerConfig (Statistical parameters) and DecisionPolicy (Business parameters). A business stakeholder can modify DecisionPolicy to change system behavior without touching mathematical logic (Open/Closed Principle). ScorerConfig is owned by the Analytics layer. DecisionPolicy is owned by the Decision Intelligence layer.

## Frozen Engineering Principles
1. Layers communicate only via strongly-typed immutable contracts.
2. No layer performs work belonging to another layer.
3. No layer communicates backwards.
4. Mathematical algorithms are immutable; business policies are configurable.
5. Evidence objects are never modified after creation.
6. Every report section carries provenance metadata.
7. The orchestrator is a pure pipeline coordinator containing zero business logic.
8. Parity validation is required before any architectural change.
9. Contract narrowing enforces information hiding between layers.
10. The Content Engine imports no mathematical or statistical libraries.
