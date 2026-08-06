# Forecast Review & Decision Support System

## Prompt Trail & Architectural Reasoning Document

## 1. Generative AI Prompt History (Project Build Record)

This section serves as a historical record of the primary prompts provided to the AI assistant to architect, implement, and verify this system. These prompts document the evolution from the initial concept to the Enterprise Decision Intelligence Engine.

### Phase: Enterprise AI Infrastructure Layer
**Prompt 1:**
> "You are the Principal Software Architect and Technical Lead responsible for completing the Enterprise AI Infrastructure Layer of the Forecast Review & Decision Support System. This is NOT a feature implementation task. This is an enterprise infrastructure sprint. The objective is to transform the existing provider abstraction into a scalable AI infrastructure capable of supporting multiple providers, observability, execution benchmarking, auditing, and future production deployment without requiring architectural refactoring."

**Prompt 2 (Refinements):**
> "incorporate the following architectural refinements before implementation: Keep storage/ as a top-level infrastructure directory, separate from reports/. Replace random or sequential execution IDs with timestamp + short UUID format (RUN-YYYYMMDD-HHMMSS-XXXX). Introduce an immutable ExecutionContext model... Add a StorageManager service... Expand ProviderMetrics and PipelineExecutionMetrics..."

### Phase: Independent Verification & Validation (IV&V)
**Prompt 3:**
> "# Enterprise Independent Verification & Validation (IV&V) Prompt
> Role: You are acting as an Independent Enterprise Verification Team... Your responsibility is to perform an independent enterprise-grade audit of the Forecast Review & Decision Support System exactly as an external verification organization would prior to approving the system for production deployment."

**Prompt 4 (IV&V Additions):**
> "Proceed with the IV&V audit after incorporating these five additions: Introduce an evidence matrix... Expand the analytics audit to include business-level validation... Add a comprehensive failure injection matrix... Include a dedicated Demo Readiness Assessment... Conclude with a Production Gap Analysis..."

### Phase: Enterprise Architecture Review
**Prompt 5:**
> "# Enterprise Architecture Review Prompt: Forecast Decision Intelligence Platform
> Role: You are an independent enterprise architecture review board... Your responsibility is to critically evaluate the current product, architecture, user experience, and long-term strategy, then propose the next-generation architecture for an enterprise Forecast Decision Intelligence Platform."

### Phase: Decision Intelligence Engine (`model_scorer.py`)
**Prompt 6:**
> "You are no longer acting as an implementation engineer. You are now acting as the following people simultaneously: Principal Forecast Analytics Consultant, Principal Data Scientist, Principal Statistician... Your task is to independently review, challenge, validate and improve the statistical methodology implemented inside model_scorer.py. ... The required business output is: Determine which forecasting model should be recommended..."

**Prompt 7 (Bug Fix & Recalibration):**
> "model_scorer.py is bullshit , please fix that" *(Note: Resolved an issue where Hit10 normalization bounds were inverted, causing lower performance to score artificially higher).*

### Phase: Documentation Synchronization
**Prompt 8:**
> "please update all the documentation of the project as well as the requirements.txt"

---

## 2. System Prompt Strategy (The MASTER_SUMMARY_PROMPT)

The runtime prompt strategy enforces a strict separation between deterministic analytics and generated narrative.

> Python = Truth  
> LLM = Narrative

The LLM does not calculate, score, validate, or infer missing facts. It receives structured outputs from Python analytics modules and converts those outputs into readable business language.

### Core Architecture Update: The Single Master Prompt

Historically, this system relied on 6 individual prompts (Executive, Risk, Comparison, Recommendation, Regional Insight, Management Narrative). This approach was deprecated and replaced with a **Single Master Prompt (`MASTER_SUMMARY_PROMPT`)** enforcing a strict JSON output schema.

## 3. Architecture Decision Record (ADR): Moving to a Master Prompt

| Decision | Move from 6 sequential prompts to 1 Master JSON Prompt |
|---|---|
| **Context** | Making 6 independent HTTP calls to an LLM provider was slow, expensive, and fragile. Network interruptions during step 4 (out of 6) required complex rollback or partial-state recovery logic. |
| **Action** | We implemented `MASTER_SUMMARY_PROMPT`, forcing the LLM to write all 4 critical narrative sections (executive summary, risk explanation, comparison, recommendations) in a single unified JSON output payload (`SummaryBundle`). |
| **Outcome** | Reduced API latency by ~80%, significantly lowered token costs, and eliminated partial-failure states. The JSON format allows strict schema validation via Pydantic (`ResponseParser`). |
| **Trade-offs** | Requires a more sophisticated `ResponseCleaner` to strip markdown fences (````json`) returned by chat-aligned models. |

## 4. Core Principle

| Layer | Responsibility |
|---|---|
| Python | Metrics, calculations, risk scoring, comparisons, drift detection, recommendation candidates, decision intelligence (model_scorer.py). |
| LLM | Summaries, explanations, executive narratives, management-ready wording formatted strictly in JSON. |

## 5. AI Responsibilities

### Allowed AI Responsibilities
| Allowed Use | Description |
|---|---|
| Summaries | Summarize verified analytics outputs. |
| Explanations | Explain why metrics or risks matter. |
| Recommendations | Phrase Python-generated recommendation candidates for management. |
| JSON Serialization | Output all narrative in a strictly defined JSON string. |

### Not Allowed AI Responsibilities
| Not Allowed | Reason |
|---|---|
| Calculations | Must be performed by Python for auditability. |
| Markdown Text | System expects parsed JSON; plain text or raw markdown will fail validation. |
| Risk Scores | Must be produced by `risk.py` or review logic. |
| Fabricated context | The LLM must not invent regions, causes, actions, or performance values. |

## 6. The Master Summary Prompt Structure

### Inputs (Injected by PromptBuilder)

| Input | Source |
|---|---|
| Forecast health score | Forecast Review Engine |
| Key risk level | `risk.py` |
| Comparison table | `comparison.py` |
| Recommendation candidates | `recommendations.py` |

### Guardrails

| Guardrail | Requirement |
|---|---|
| JSON strictness | Must parse cleanly in Python's `json.loads`. |
| No calculations | Do not compute or alter metrics. |
| No invented context | Use only supplied facts. |

## 7. Context Injection Strategy

The `PromptBuilder` injects context in structured sections:

```text
Forecast Metadata:
{metadata}

Performance Metrics:
{performance_metrics}

Comparison Results:
{comparison_results}

Risk Assessment:
{risk_assessment}

Recommendation Candidates:
{recommendation_candidates}
```

## 8. LLM Model Strategy

### ProviderChain Resilience

The architecture utilizes a `ProviderChain` that cascades through configured LLMs. 
- **Primary:** Gemini (`gemini-2.5-pro` / `gemini-1.5-pro`) — Excellent at following strict JSON adherence instructions.
- **Failover:** Company Provider (`llama3.1:8b` via Ollama/Local) — Robust local fallback for network partitions or primary service outages.

Because both models receive the same prompt and are piped through the same `ResponseCleaner`, the application orchestrator doesn't need to know which model ultimately generated the JSON.
