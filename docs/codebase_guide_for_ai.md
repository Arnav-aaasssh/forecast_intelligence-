# Enterprise Decision Intelligence: AI Codebase Guide

## 1. Project Overview & Architectural Philosophy
This project implements an **Enterprise Decision Intelligence Platform**. Its core philosophy is strict decoupling and immutability. Data flows in a unidirectional pipeline through distinct, isolated engines:
1. **Analytics Engine:** Computes "what is true" (math, statistics, metrics).
2. **Decision Engine:** Computes "what to do" (evaluates metrics against policies to authorize actions).
3. **Content Engine:** Computes "how to explain it" (generates deterministic, template-based natural language reports).
4. **Presentation/Renderer (Future/Downstream):** Determines "how it looks" (PDF, UI, Markdown).

**Strict Rules for AI Agents:**
* **No Leakage:** The Content Engine cannot do math. The Decision Engine cannot generate text. The Analytics Engine cannot evaluate business policy.
* **Immutability:** Data structures passed between engines are strictly frozen dataclasses (`@dataclass(frozen=True)`). You must not mutate state.
* **Determinism:** No LLM-based hallucination or subjective adjectives are allowed in the core engines. Text generation relies on deterministic `.format()` template injection.

---

## 2. Directory Structure & File Purposes

### `core/contracts/`
This is the most critical directory. It defines the immutable interfaces passed between the engines. If you change a contract here, you break the pipeline.
* **`analytics.py`**: Defines `ForecastAccuracyResult`, `StatisticalAnalyticsResult`, and `AnalyticalEvidenceBundle`. These contain raw numbers (WAPE, Bias, Hit Rate, p-value).
* **`decision.py`**: Defines `PolicyEvaluation`, `PolicyEvaluationMatrix`, and `DecisionContract`. These encapsulate business logic outcomes (e.g., `PASS`/`FAIL` for confidence) and final state decisions (e.g., `DEPLOY_GLOBAL`, `RETAIN_MANUAL`).
* **`content.py`**: Defines `BusinessQuestionContract`, `EvidenceMetric`, `StructuredSection`, and `ReportDocument`. These are the structures used for report assembly.
* **`dataset.py`**: Defines data references (`DatasetReference`) and evaluation windows.

### `core/analytics/`
Calculates statistical and accuracy metrics.
* **`engine/`**: Contains the orchestrators for analytics computations. It ingests prepared datasets and emits the `AnalyticalEvidenceBundle`.

### `core/decision/`
Evaluates analytics against configured business policies to authorize an operational change.
* **`policy/engine.py`**: Contains the `DecisionPolicyEngine` and specific business policies (e.g., ML Superiority, Minimum Confidence, Required Coverage). It consumes the `AnalyticalEvidenceBundle` and generates a `PolicyEvaluationMatrix`.
* **`synthesis/synthesizer.py`**: Contains the `DecisionSynthesizer` and `DecisionStateMachine`. It consumes the matrix and emits a terminal `DecisionContract` (e.g., "Deploy Global", "Deploy Pilot").

### `core/content/engine/`
Translates the hard numbers and decisions into human-readable, immutable text sections.
* **`generators.py`**: Contains individual generators (`EvidenceGenerator`, `ObservationGenerator`, `ConclusionGenerator`, `DecisionProjectionGenerator`). They extract data and inject it into predefined string templates.
* **`orchestrator.py`**: The `ContentOrchestrator` that wires the generators together to produce a `StructuredSection`.
* **`assembly.py`**: The `ReportAssemblyEngine` which orders, deduplicates, and aggregates multiple `StructuredSection`s into a single `ReportDocument`.

### `core/foundation/` & `core/validation/`
* **`execution_context.py` (foundation)**: Manages `ExecutionContext`. Every contract carries an execution context and traceability UUID. This acts as an unforgeable passport guaranteeing the data was not tampered with.
* **`exceptions.py` (validation)**: Deterministic error handling. We raise specific errors (e.g., `AnalyticsException`, `ContractValidationException`) rather than silently fixing or ignoring missing data.

### `tests/`
Comprehensive pytest suites ensuring 100% adherence to the rules above. Look here to understand edge cases (e.g., missing evidence falling back to `N/A`, suppressed recommendations).

---

## 3. Data Flow & Orchestration Guide

To understand how to integrate a new feature, you must understand the exact sequence of orchestration.

**Step 1: Analytics Execution**
1. System passes data references to the Analytics Engine.
2. Analytics computes metrics and packages them into an `AnalyticalEvidenceBundle` (found in `core/contracts/analytics.py`).
*Note: This bundle is mathematically complete but contains no opinions or actions.*

**Step 2: Policy Evaluation**
1. The `DecisionPolicyEngine` (`core/decision/policy/engine.py`) reads the `AnalyticalEvidenceBundle`.
2. It runs a registry of active policies (e.g., Is WAPE > 10%? Is p-value < 0.05?).
3. It emits a `PolicyEvaluationMatrix`.

**Step 3: Decision Synthesis**
1. The `DecisionSynthesizer` (`core/decision/synthesis/synthesizer.py`) reads the `PolicyEvaluationMatrix`.
2. A deterministic State Machine evaluates the pass/fail matrix to output a final `DecisionContract` (e.g., if ML is superior but confidence is low -> `PILOT`).

**Step 4: Content Generation**
1. The `ContentOrchestrator` (`core/content/engine/orchestrator.py`) takes three things: the `AnalyticalEvidenceBundle`, the `DecisionContract`, and a configured `BusinessQuestionContract`.
2. It passes them through the Generators (`generators.py`).
3. Evidence is extracted. Templates are formatted (e.g., "Model A achieved {primary_wape} WAPE").
4. A `StructuredSection` is emitted.

**Step 5: Report Assembly**
1. The `ReportAssemblyEngine` (`core/content/engine/assembly.py`) takes an array of `StructuredSection` objects.
2. It checks for mandatory blocks, removes duplicates, validates that traceability UUIDs match perfectly, and packages them into a `ReportDocument`.

## 4. How to Build a New Feature

If you are asked to integrate a new feature (e.g., adding a new Business Question, or a new Statistical Policy):

**Adding a New Business Question (e.g., Q5):**
* **Do NOT** write NLP generation code.
* **Do** create a new `BusinessQuestionContract` configuration mapping the necessary metric keys to specific sentence templates. The Content Engine will blindly render it.

**Adding a New Business Policy:**
* **Do NOT** add `if` statements inside the Synthesizer or Content engines.
* **Do** implement a new policy class inheriting from the policy base, register it in `DecisionPolicyEngine`, and let the existing State Machine naturally handle the new `PolicyEvaluation` matrix result.

**Modifying Content Formatting:**
* **Do NOT** inject Markdown or HTML tags into the Content Engine (`generators.py`).
* **Do** wait for the eventual Presentation Renderer phase, as the `StructuredSection` and `ReportDocument` must remain format-agnostic.
