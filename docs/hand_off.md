# Forecast Review & Decision Support System

## Project Handoff Document

## 1. Project Overview

The Forecast Review & Decision Support System is an enterprise-grade, Teams-driven application that evaluates existing forecasts, identifies forecast risk, compares forecast approaches, generates management insights, and delivers recommendations through Microsoft Teams.

The system is designed around a clear operating principle:

> Python = Truth  
> LLM = Narrative

Python performs all calculations, metrics, absolute scoring, statistical confidence testing, comparisons, and deterministic recommendation logic. The LLM subsystem is used exclusively to explain and summarize verified analytics outputs in a clear, management-ready narrative.

### Current Status

| Area | Status |
|---|---|
| Architecture Design | Completed (Enterprise Ready) |
| Implementation | Completed |
| Decision Intelligence Engine | Completed (Winsorized Min-Max, Wilcoxon) |
| Enterprise Resilience Layer | Completed (ProviderRegistry, CircuitBreakers) |
| IV&V Audit | Passed (Production Ready) |
| MVP Storage Decision | SharePoint |
| Primary API endpoint | `POST /weekly-review` |

## 2. Business Context

Forecasts influence operational, financial, regional, and executive decisions. Existing forecast processes may produce outputs that need review before decisions are made. This project exists to create a consistent review and governance layer over those forecasts.

The system helps business stakeholders answer:

| Business Question | System Response |
|---|---|
| Can this forecast be trusted? | Forecast health score and risk assessment. |
| What has changed? | Drift and history analysis. |
| Which approach is better? | `model_scorer.py` Decision Intelligence output. |
| What should management do? | Recommendation section and executive narrative. |
| Which regions need attention? | Regional insights where data supports them. |

## 3. Key Decisions Made (Architecture Decision Records)

| Decision | Outcome | Rationale |
|---|---|---|
| Forecast Review vs Forecast Generation | Build a review system, not a forecasting engine. | The business need is governance and decision support over existing forecasts. |
| Python Analytics vs LLM Analytics | Python owns all calculations. | Deterministic calculations are auditable and testable. |
| Decision Intelligence Scoring | Implemented Absolute Scoring (`model_scorer.py`). | Fixes Independence of Irrelevant Alternatives (IIA) violations present in rank-based scoring. |
| Confidence Testing | Combined Wilcoxon p-values with win rates. | Ensures statistical significance before declaring a challenger better than a baseline model. |
| Provider-Agnostic LLM | Use a `ProviderChain` instead of a hardcoded LLM. | Ensures failover resilience across primary (Gemini) and secondary (Company) models. |
| Strict JSON Outputs | Use `MASTER_SUMMARY_PROMPT` to enforce JSON. | Allows Pydantic parsing (`ResponseParser`) to guarantee structural integrity of narratives. |
| Infrastructure Decoupling | Implemented `StorageManager` and `ExecutionContext`. | Decouples business logic from filesystem I/O and provides immutable telemetry across the pipeline. |

## 4. Architecture Explanation

Microsoft Teams is the front door for users. A user uploads a forecast file, such as `Forecast_Week_32.xlsx`, through Teams. The file is stored in SharePoint under `ForecastReview/InputFiles/`. Power Automate detects the file creation event, retrieves the file content, and calls the FastAPI backend using `POST /weekly-review`.

The Analytics Engine produces objective outputs such as performance metrics, comparison results, drift indicators, historical patterns, holiday context, risk indicators, insights, and recommendation candidates. The **Model Scorer** then evaluates and recommends the statistically optimal forecast. The Forecast Review Engine consolidates those outputs into a structured package.

The prompt layer then injects verified analytics outputs into the `MASTER_SUMMARY_PROMPT`. The `ProviderChain` coordinates the LLM request (applying `CircuitBreaker` and `RetryPolicy` rules), and the selected LLM generates a strict JSON payload. The payload is cleaned by `ResponseCleaner`, parsed by `ResponseParser` into a `SummaryBundle`, and then rendered into Markdown, HTML, and JSON reports. The reports are stored back in SharePoint via the `StorageManager` and the completion response is posted back to Teams.

### Plain-Text Runtime Flow

```text
Teams file upload
  -> SharePoint InputFiles
  -> Power Automate file-created trigger
  -> FastAPI POST /weekly-review
  -> Forecast Review Engine
  -> Python analytics modules (Performance, Drift, Risk, etc.)
  -> Decision Intelligence Engine (model_scorer.py)
  -> ProviderChain (Gemini -> Failover)
  -> ResponseCleaner & ResponseParser (SummaryBundle)
  -> Markdown, HTML, JSON Generation
  -> StorageManager -> SharePoint
  -> Teams notification
```

## 5. Recommended Folder Structure

```text
forecast_review/
  app.py
  model_scorer.py             # Enterprise Decision Intelligence Engine
  ivv_audit.py                # Verification & Validation harness
  analytics/
    performance.py
    comparison.py
    drift.py
    history.py
    risk.py
    insights.py
    recommendations.py
  infrastructure/
    storage_manager.py
    execution_context.py
  llm/
    llm_service.py
    prompt_builder.py
    prompts.py
    llm_provider.py
    provider_chain.py
    provider_registry.py
    retry.py
    circuit_breaker.py
    response_cleaner.py
    response_parser.py
  models/
    summary_models.py
    provider_metrics.py
  reports/
    markdown_generator.py
    html_report.py
    json_report.py
  config/
  tests/
  docs/
    Design_system.md
    hand_off.md
    prompt_trail.md
    technical_md.md
    analytics_schema.md
```

## 6. Dependencies

The exact python versions required to run the deterministic engine have been frozen into `requirements.txt`. Key dependencies include:

| Dependency | Use |
|---|---|
| FastAPI | Backend API framework. |
| Pandas / NumPy | Data loading, transformation, tabular analytics, and vector math. |
| SciPy | Wilcoxon signed-rank testing for statistical confidence. |
| Google Generative AI | Primary LLM Provider SDK. |
| Pydantic | JSON schema validation and data parsing. |
| Uvicorn | ASGI server for FastAPI. |

## 7. Deployment Expectations

### Shared Server / Production Ready

| Area | Expectation |
|---|---|
| Hosting | Internal VM, Azure VM, or enterprise-approved platform. |
| API | Persistent FastAPI service. |
| LLM | Connected via secure internal networking and CircuitBreakers (via `ProviderRegistry`). |
| Storage | SharePoint remains document repository, abstracted behind `StorageManager`. |
| Operations | Monitored via `ExecutionContext` execution IDs (`RUN-YYYYMMDD-HHMMSS-XXXX`). |

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM hallucination | Incorrect narrative may mislead users. | Inject only verified analytics context, require strict JSON guardrails, and bypass LLM for core calculations. |
| IIA Violations | Rank-based scoring can result in worse models winning. | Implemented Winsorized Min-Max absolute normalization in `model_scorer.py`. |
| Cascading LLM Failures | Upstream API outages can bring down the application. | Integrated CircuitBreakers and primary/secondary ProviderChains. |

## 9. Project Status & Roadmap

The system has successfully completed its Enterprise Infrastructure Sprint and IV&V Audit. It has transitioned from a theoretical MVP to a hardened, resilient, statistically sound enterprise architecture.

**Completed Milestones:**
- Dataset ingestion & Schema validation.
- Deterministic analytics pipeline (Performance, Comparison, Drift, History, Risk).
- Single Master Prompt architecture enforcing strict JSON parsing.
- Enterprise-grade resilience (RetryPolicy, CircuitBreaker, Failover).
- Markdown, HTML, and JSON artifact generation.
- **Enterprise Architecture Review & IV&V Audit** (Verified ready for production).
- **Decision Intelligence Engine** (Absolute Scoring, Wilcoxon confidence testing, baseline fallback).

**Future Roadmap:**
- Containerization (Docker deployment readiness).
- SQL Database integration replacing SharePoint document storage (StorageManager simplifies this transition).
- Interactive Follow-up Question LLM Chatbot via `/ask-question`.

## 10. Ownership Recommendations

| Role | Responsibility |
|---|---|
| Product Owner | Prioritization, roadmap scope, stakeholder alignment. |
| Solution Architect | Architecture integrity and enterprise fit. |
| Technical Lead | Backend implementation and code quality. |
| Analytics Lead | Forecast metrics, Decision Intelligence scoring, and validation logic. |
| Prompt Owner | Prompt templates, guardrails, and narrative quality. |
| Operations Owner | Deployment, monitoring (`ExecutionContext`), and support readiness. |
