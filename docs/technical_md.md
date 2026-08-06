# Forecast Review & Decision Support System

## Technical Architecture Document

## 1. Technical Architecture

The Forecast Review & Decision Support System is a Microsoft Teams-driven, API-backed, Python analytics application with a provider-agnostic LLM narrative layer. It evaluates existing forecasts and returns a structured forecast review package.

The core technical principle is:

> Python = Truth  
> LLM = Narrative

All calculations, metrics, risk scores, comparisons, and deterministic recommendations are produced by Python. The LLM only generates narrative based on verified context, outputting strict JSON that is parsed and formatted.

## 2. System Overview

The system processes weekly forecast review files through a Teams and SharePoint workflow. A user uploads a forecast file in Teams, SharePoint stores the file, Power Automate detects the upload, and FastAPI executes the Forecast Review Engine. Python analytics modules calculate the truth layer. The Provider-agnostic LLM chain converts the structured analytics package into strict JSON narrative bundles. Reports and analytics outputs are generated deterministically and stored back in SharePoint, surfaced to users through Teams.

```text
Teams upload
  -> SharePoint InputFiles
  -> Power Automate
  -> FastAPI POST /weekly-review
  -> Forecast Review Engine
  -> Python Analytics
  -> LLM JSON Narrative Bundle
  -> Report Generator (Markdown, HTML, JSON)
  -> SharePoint Reports and AnalyticsResults
  -> Teams response
```

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Microsoft Teams | User file upload, notification, and response channel. |
| Storage | SharePoint | MVP storage for input files, analytics results, reports, and audit logs. |
| Workflow | Power Automate | Orchestration between SharePoint, Teams, and FastAPI. |
| API Layer | FastAPI | Backend endpoints and request processing. |
| Analytics Layer | Python, Pandas, NumPy, Scikit-Learn | Deterministic data analysis and review logic. |
| AI Layer | ProviderChain (Gemini, Company) | Configurable, failover-ready LLM narrative generation. |
| Reporting Layer | HTML, JSON, Markdown generators | Formats review outputs for SharePoint and Teams. |
| Runtime | Uvicorn | ASGI server for FastAPI. |

## 4. Layer Descriptions

### Frontend: Microsoft Teams

Teams provides the business user interface. It supports forecast file upload, review completion notification, and access to the completed Forecast Review Package.

### Storage: SharePoint

SharePoint stores MVP input and output artifacts.

| Folder | Purpose |
|---|---|
| `ForecastReview/InputFiles/` | Uploaded forecast datasets. |
| `ForecastReview/AnalyticsResults/` | Structured Python analytics outputs. |
| `ForecastReview/Reports/` | Generated HTML Forecast Review Packages. |
| `ForecastReview/AuditLogs/` | Processing and traceability records. |

### Workflow: Power Automate

Power Automate detects SharePoint file creation, retrieves file content, calls FastAPI, handles success and error responses, stores outputs, and posts completion messages back into Teams.

### API Layer: FastAPI

FastAPI provides the service boundary. It validates inputs, invokes processing, handles errors, and exposes operational endpoints.

### Analytics Layer: Python

The analytics layer is authoritative. It contains deterministic modules for forecast performance, manual vs ML comparison, drift, history, holiday impact, forecaster performance, risk, insights, and recommendations.

### AI Layer: Provider-Agnostic LLM Chain

The LLM subsystem uses a `ProviderChain` that routes prompts to the primary provider (e.g., Gemini) or fails over to a secondary provider (e.g., Company Llama). The models receive only validated analytics context via a single `MASTER_SUMMARY_PROMPT` and return strict JSON strings.

### Reporting Layer

The reporting layer generates HTML, canonical JSON, and Markdown artifacts directly from immutable data models (`SummaryBundle`, `ReviewResult`). The LLM never writes files directly.

## 5. Detailed Architecture View

### Runtime Architecture Flow

```text
User
  -> Microsoft Teams
  -> SharePoint InputFiles folder
  -> Power Automate
  -> FastAPI
  -> Request validation and schema mapping
  -> Forecast Review Engine
  -> Python Analytics Engine
       - performance.py
       - comparison.py
       - drift.py
       - history.py
       - holiday.py
       - forecaster.py
       - risk.py
       - insights.py
       - recommendations.py
  -> Consolidated Forecast Review Package
  -> Prompt Builder (MASTER_SUMMARY_PROMPT)
  -> ProviderChain (Gemini -> Failover)
  -> ResponseCleaner
  -> ResponseParser
  -> SummaryBundle
  -> MarkdownGenerator / HTML Generator
  -> SharePoint Reports, AnalyticsResults, and AuditLogs folders
  -> Microsoft Teams notification and summary
```

### Architecture Interaction Matrix

| Layer | Component | Primary Responsibility | Output |
|---|---|---|---|
| User Interaction | Microsoft Teams | File upload, notifications, and follow-up entry point | Uploaded forecast file and user request |
| Storage | SharePoint | Store input files, generated reports, analytics outputs, and audit logs | Controlled document repository |
| Workflow | Power Automate | Detect file creation, retrieve content, call API, post results | Orchestrated review request |
| API | FastAPI | Validate request, load dataset, invoke review workflow | Review processing response |
| Orchestration | Forecast Review Engine | Execute modules and consolidate outputs | Structured analytics package |
| Analytics | Python modules | Calculate metrics, risk, drift, insights, and recommendation candidates | Deterministic review facts |
| AI | ProviderChain | Generates JSON narrative from supplied facts | Immutable SummaryBundle |
| Reporting | Report Generators | Format HTML, Markdown, or Teams-ready output | Forecast Review Package |

## 6. API Design

### POST `/weekly-review`

Processes a weekly forecast file uploaded through Teams and stored in SharePoint.

#### Input Schema

```json
{
  "request_id": "string",
  "requested_by": "string",
  "source": {
    "sharepoint_site": "string",
    "file_path": "ForecastReview/InputFiles/Forecast_Week_32.xlsx",
    "file_name": "Forecast_Week_32.xlsx",
    "file_content_base64": "string"
  },
  "review_context": {
    "fiscal_year": "string",
    "fiscal_week": "string",
    "review_type": "weekly_review"
  },
  "options": {
    "include_holiday_context": true,
    "include_regional_insights": true,
    "write_report_to_sharepoint": true
  }
}
```

#### Required Dataset Columns

The API must validate that the uploaded file contains the required columns before analytics execution.

| Column | Required For |
|---|---|
| `Forecast_Name` | Forecast identification |
| `Fiscal_Year` | Fiscal year context |
| `Fiscal_Week` | Weekly review context |
| `Region` | Regional analysis |
| `Country` | Country-level grouping |
| `Offering` | Offering-level grouping |
| `Channel` | Channel-level grouping |
| `Forecaster` | Forecaster performance evaluation |
| `Manual_Forecast` | Manual forecast accuracy |
| `ML_Forecast` | ML forecast accuracy |
| `Previous_Forecast` | Drift analysis |
| `Actual_Offered` | Accuracy calculation |
| `Holiday_Count` | Holiday impact analysis |
| `Risk_Flag` | Existing business risk signal |
| `Risk_Category` | Existing business risk classification |
| `Mean (Hist Contacts)` | Volatility calculation |
| `Std Dev (Hist Contacts)` | Volatility calculation |

Optional historical fields `Final_Y1` through `Final_Y5` should be used by `history.py` when present.

#### Output Schema

```json
{
  "request_id": "string",
  "status": "success",
  "report": {
    "title": "Forecast Review Package",
    "format": "html",
    "sharepoint_path": "ForecastReview/Reports/Forecast_Week_32_review.html",
    "teams_summary": "string"
  },
  "analytics_package": {
    "forecast_health": {},
    "performance": {},
    "comparison": {},
    "drift": {},
    "history": {},
    "holiday": {},
    "forecaster": {},
    "risk": {},
    "insights": {},
    "recommendations": {}
  },
  "audit": {
    "analytics_version": "string",
    "prompt_version": "string",
    "model": "llama3.1",
    "source_file": "Forecast_Week_32.xlsx"
  }
}
```

#### Example Payload

```json
{
  "request_id": "FR-2026-W32-001",
  "requested_by": "forecast.manager@example.com",
  "source": {
    "sharepoint_site": "ForecastReview",
    "file_path": "ForecastReview/InputFiles/Forecast_Week_32.xlsx",
    "file_name": "Forecast_Week_32.xlsx",
    "file_content_base64": "<base64 file content>"
  },
  "review_context": {
    "fiscal_year": "2026",
    "fiscal_week": "32",
    "review_type": "weekly_review"
  },
  "options": {
    "include_holiday_context": true,
    "include_regional_insights": true,
    "write_report_to_sharepoint": true
  }
}
```

### POST `/ask-question`

Supports follow-up questions against a completed review package where enabled.

#### Input Schema

```json
{
  "request_id": "string",
  "review_id": "string",
  "question": "string",
  "requested_by": "string"
}
```

The endpoint must answer only from the completed review context. It must not trigger new calculations unless explicitly routed through a new review request.

### GET `/health`

Returns service health.

```json
{
  "status": "ok"
}
```

### GET `/version`

Returns API, analytics, prompt, and model configuration versions.

```json
{
  "api_version": "0.1.0",
  "analytics_version": "0.1.0",
  "prompt_version": "0.1.0",
  "model": "ollama-model-name"
}
```

## 7. Analytics Engine Design

### `performance.py`

| Item | Description |
|---|---|
| Purpose | Forecast accuracy analysis. |
| Inputs | `Manual_Forecast`, `ML_Forecast`, `Actual_Offered`, fiscal period, and grouping fields. |
| Outputs | Manual accuracy, ML accuracy, forecast error, forecast health score inputs. |
| Processing Logic | Validate actual values, calculate accuracy using `Accuracy = 1 - ABS(Forecast - Actual) / Actual`, compare manual and ML performance, and return structured metrics. |

### `comparison.py`

| Item | Description |
|---|---|
| Purpose | Compare manual and ML forecasting approaches. |
| Inputs | Manual forecast performance, ML forecast performance, grouping fields, and review period. |
| Outputs | ML vs manual performance, win rate, best forecast method where supported by metrics. |
| Processing Logic | Compare manual and ML accuracy and error measures by period and grouping, calculate win rate, and identify the better performing method only when supported by Python results. |

### `drift.py`

| Item | Description |
|---|---|
| Purpose | Forecast revision and instability analysis. |
| Inputs | `Previous_Forecast`, `Manual_Forecast`, `ML_Forecast`, fiscal period, and grouping fields. |
| Outputs | Largest forecast changes, forecast instability indicators, revision tracking. |
| Processing Logic | Calculate drift using `(Current Forecast - Previous Forecast) / Previous Forecast`, classify drift severity, and identify records or groups with significant revision movement. |

### `history.py`

| Item | Description |
|---|---|
| Purpose | Historical benchmark and trend analysis. |
| Inputs | `Final_Y1`, `Final_Y2`, `Final_Y3`, `Final_Y4`, `Final_Y5`, current forecast values, and grouping fields. |
| Outputs | Historical deviation, trend direction, abnormal forecast detection. |
| Processing Logic | Compare current forecast behavior with historical values, evaluate trend direction, and flag abnormal deviations where history is available. |

### `holiday.py`

| Item | Description |
|---|---|
| Purpose | Holiday impact analysis. |
| Inputs | `Holiday_Count`, fiscal period, region, and country. |
| Outputs | Holiday risk, seasonality impact, demand distortion indicator. |
| Processing Logic | Evaluate holiday count and affected periods to identify potential external demand disturbance. |

### `forecaster.py`

| Item | Description |
|---|---|
| Purpose | Forecaster performance assessment. |
| Inputs | `Forecaster`, manual adherence or accuracy outputs, ML adherence or accuracy outputs, and historical performance where available. |
| Outputs | Forecaster rankings, consistency scores, performance trends. |
| Processing Logic | Aggregate performance by forecaster, evaluate consistency, and return ranked forecaster performance indicators. |

### `risk.py`

| Item | Description |
|---|---|
| Purpose | Convert analytics outputs into risk indicators and risk scores. |
| Inputs | Accuracy, drift, volatility, holiday impact, and existing risk fields where supplied. |
| Outputs | Risk score, risk category, risk drivers, risk ranking. |
| Processing Logic | Apply deterministic risk scoring: accuracy risk, drift risk, volatility risk, and holiday risk. Final risk score uses the configured weighting of 40% accuracy, 20% drift, 20% volatility, and 20% holiday risk. |

### `insights.py`

| Item | Description |
|---|---|
| Purpose | Generate business insight findings from analytics outputs. |
| Inputs | Metrics, drift, risk, history, holiday context, regional data. |
| Outputs | Insight list with evidence and affected dimensions. |
| Processing Logic | Apply rule-based logic only. Example: if accuracy is low, drift is high, and risk score is elevated, emit a high-risk region finding with supporting evidence. |

### `recommendations.py`

| Item | Description |
|---|---|
| Purpose | Generate management recommendation candidates from verified analytics. |
| Inputs | Risk outputs, insight candidates, comparison results, forecast health score. |
| Outputs | Prioritized recommendation candidates and supporting rationale. |
| Processing Logic | Apply deterministic rules, such as `Risk Score > 80` means immediate review required, `Drift > 15%` means validate demand drivers, and `Accuracy < 70%` means revisit forecast assumptions. |

### `model_scorer.py`

| Item | Description |
|---|---|
| Purpose | Decision Intelligence Engine for enterprise model selection. |
| Inputs | Forecasts, Actuals, historical WAPE, Bias, IQR, Hit10. |
| Outputs | Absolute Composite Score, Recommended Model, Multi-metric win reasoning, Statistical confidence. |
| Processing Logic | Employs Winsorized Min-Max absolute normalization to prevent IIA violations. Uses Wilcoxon signed-rank tests combined with win-rates to evaluate significance. Reverts to baseline models if challengers lack sufficient statistical distinction. Supports Volume Tier segmentation. |

## 8. Risk Scoring Framework

Risk scoring is deterministic and implemented in Python. The LLM may explain risk but must not calculate, change, or infer risk scores.

| Risk Component | Calculation or Source | Weight |
|---|---|---|
| Accuracy Risk | `100 - Accuracy` | 40% |
| Drift Risk | Forecast revision percentage | 20% |
| Volatility Risk | `Std Dev / Historical Mean` | 20% |
| Holiday Risk | Derived from `Holiday_Count` | 20% |

### Drift Threshold Example

| Drift Range | Risk Level |
|---|---|
| 0-5% | Low |
| 5-10% | Medium |
| 10-15% | Elevated |
| 15%+ | High |

## 9. Forecast Review Engine

### Workflow

1. Receive the validated `/weekly-review` request.
2. Load the uploaded Excel dataset.
3. Validate mandatory dataset columns.
4. Run analytics modules in sequence.
5. Consolidate outputs into the analytics package.
6. Build forecast health and risk outputs.
7. Assemble the Forecast Review Package.
8. Send structured package to the prompt pipeline.
9. Generate the HTML report and Teams summary.
10. Store outputs in SharePoint.

### Pseudo-code

```python
def process_weekly_review(request):
    validated_request = validate_request(request)
    dataset = load_excel_from_request(validated_request)
    validate_required_columns(dataset)

    performance = performance_module.calculate(dataset)
    comparison = comparison_module.compare(dataset, performance)
    drift = drift_module.detect(dataset)
    history = history_module.analyze(dataset)
    holiday = holiday_module.evaluate(dataset)
    forecaster = forecaster_module.evaluate(dataset, performance)

    risk = risk_module.assess(
        performance=performance,
        comparison=comparison,
        drift=drift,
        history=history,
        holiday=holiday,
        forecaster=forecaster,
    )

    insights = insights_module.generate(
        performance=performance,
        comparison=comparison,
        drift=drift,
        history=history,
        holiday=holiday,
        forecaster=forecaster,
        risk=risk,
    )

    recommendations = recommendations_module.generate(
        risk=risk,
        insights=insights,
        comparison=comparison,
    )

    review_package = review_engine.build_package(
        performance=performance,
        comparison=comparison,
        drift=drift,
        history=history,
        holiday=holiday,
        forecaster=forecaster,
        risk=risk,
        insights=insights,
        recommendations=recommendations,
    )

    narrative_bundle = llm_pipeline.generate_all_summaries(review_package)
    markdown_report = report_renderer.generate_markdown_reports(narrative_bundle, output_dir)
    html_report = report_renderer.render_html(review_package, narrative_bundle)
    sharepoint_path = store_report(html_report, validated_request)
    return build_api_response(review_package, html_report, sharepoint_path)
```

### Processing Sequence

| Step | Component | Output |
|---|---|---|
| 1 | FastAPI | Validated `/weekly-review` request. |
| 2 | Dataset loader | Excel dataset loaded from uploaded file content. |
| 3 | Analytics modules | Metrics, drift, comparison, history, holiday, and forecaster outputs. |
| 4 | Risk module | Risk score, category, ranking, and drivers. |
| 5 | Insights module | Structured business findings. |
| 6 | Recommendations module | Management recommendation candidates. |
| 7 | Review Engine | Consolidated Forecast Review Package. |
| 8 | LLM pipeline | `SummaryBundle` (parsed JSON). |
| 9 | Report renderer | HTML report, Markdown files, and JSON dump. |
| 10 | SharePoint output | Report, analytics results, and audit logs stored. |

## 10. Enterprise AI Infrastructure & LLM Integration

### Provider-Agnostic Architecture

The LLM serving layer abstracts the provider using `BaseLLMProvider`. Requests are routed through a `ProviderChain` that handles failover (e.g., from Gemini to Company Provider). Dynamic initialization is handled by the `ProviderRegistry` utilizing Dependency Injection.

Additionally, the layer incorporates a `RetryPolicy` and `CircuitBreaker` to ensure infrastructure resilience against 5xx network errors.

### Infrastructure Refinements

| Component | Responsibility |
|---|---|
| `ExecutionContext` | Immutable data structure tracking execution IDs (RUN-YYYYMMDD-HHMMSS-XXXX), request IDs, directory states, and pipeline telemetry across all modules. |
| `StorageManager` | Centralized I/O service responsible for creating run folders, persisting artifacts, metrics, and traces, completely decoupling business logic from the filesystem. |
| `ProviderRegistry` | Factory binding configuration, Providers, Retry Policies, and Circuit Breakers into functional chains. |

### Prompt Pipeline

```text
Review Package
  -> Prompt Builder (MASTER_SUMMARY_PROMPT)
  -> Resilient Provider Proxy (CircuitBreaker + Retry)
  -> LLM Request
  -> Raw LLM Response (String)
  -> ResponseCleaner (Regex strip markdown fences)
  -> ResponseParser (JSON Loads -> Pydantic Models)
  -> SummaryBundle
```

| Stage | Responsibility |
|---|---|
| Review Package | Supplies verified analytics outputs from Python. |
| Prompt Builder | Injects context into the `MASTER_SUMMARY_PROMPT` requiring strict JSON output. |
| Resilient Proxy | Intercepts transient HTTP errors and retries. |
| LLM Request | Sends the bounded prompt to the configured provider chain. |
| Raw LLM Response | Receives JSON (often polluted with markdown). |
| ResponseCleaner | Cleans the output string deterministically. |
| ResponseParser | Validates the schema and ensures all 4 summaries exist. |
| SummaryBundle | Immutable data object returned to the orchestration layer. |

### Resilience Pipeline

| Component | Description |
|---|---|
| RetryPolicy | Applies exponential backoff with jitter on transient network/rate-limit errors. |
| CircuitBreaker | State machine (CLOSED -> OPEN -> HALF-OPEN) preventing cascading failures. |
| ProviderChain | Automatically falls back to a secondary API endpoint if the primary opens its circuit. |
| SummaryBundleFactory | Generates deterministic placeholders if a total API outage occurs. |

## 11. Error Handling

| Error Type | Handling |
|---|---|
| Invalid request | Return validation error with missing or invalid fields. |
| Unsupported file | Reject the request with a clear file type or parsing error. |
| Missing required column | Return validation failure before analytics execution. |
| Missing optional historical data | Continue processing and state that historical analysis is limited. |
| Analytics failure | Log error and return controlled failure response. |
| Ollama unavailable | Return structured analytics with narrative unavailable notice. |
| SharePoint write failure | Return review status and flag report persistence failure for retry. |
| Power Automate failure | Log API response status and provide retry guidance at workflow level. |

## 12. Security

### Authentication

MVP authentication should be defined before pilot use. For enterprise use, integrate with approved identity and access patterns.

### API Protection

| Control | Recommendation |
|---|---|
| API key or token | Protect FastAPI endpoints from unauthenticated calls. |
| Network restriction | Restrict access to internal networks where possible. |
| Input validation | Use schema validation for all request payloads. |
| Secrets handling | Store credentials outside source code. |

### Logging

Log request IDs, timestamps, processing status, validation failures, module failures, prompt versions, and model identifiers. Do not log sensitive forecast data unless approved by governance policy.

### Audit Trail

Each review should capture:

| Audit Field | Purpose |
|---|---|
| Request ID | Traceability. |
| Source file | Input file traceability. |
| SharePoint output path | Report and artifact traceability. |
| Analytics version | Reproducibility. |
| Prompt version | Narrative traceability. |
| Model name | LLM governance. |
| Timestamp | Operational audit. |
| Requesting user | Accountability, subject to privacy policy. |

## 13. Deployment Options

| Option | Description | Use Case |
|---|---|---|
| Local Machine | FastAPI and Ollama run locally. | Developer MVP. |
| Shared Workstation | Shared host for pilot users. | Small controlled pilot. |
| Internal VM | Dedicated internal server. | Team-level production candidate. |
| Azure VM | Cloud-hosted VM under enterprise controls. | Future scalable deployment. |

SharePoint remains the MVP storage layer across deployment options unless a future enterprise database is approved.

## 14. CI/CD Strategy

| Area | Recommendation |
|---|---|
| Source control | Version application code, prompts, and docs. |
| Automated tests | Run unit and integration tests on every change. |
| Packaging | Build repeatable deployment artifacts. |
| Environment config | Separate local, pilot, and enterprise settings. |
| Release notes | Document analytics and prompt changes. |

## 15. Monitoring

Monitor:

| Metric | Purpose |
|---|---|
| API availability | Confirm service is reachable. |
| Request latency | Track review processing time. |
| SharePoint read/write status | Track input retrieval and report persistence. |
| Analytics failures | Detect module-level issues. |
| LLM failures | Detect Ollama availability or response problems. |
| Validation errors | Identify user input or workflow issues. |

## 16. Performance Considerations

### Target Processing Times

| Process Area | Target |
|---|---|
| Dataset validation | Less than 30 seconds |
| Analytics processing | Less than 3 minutes |
| Report generation | Less than 5 minutes |
| LLM summary | Less than 30 seconds |
| Follow-up questions | Less than 15 seconds |

| Area | Consideration |
|---|---|
| Data size | Large forecast datasets may require batching or async processing. |
| LLM latency | Narrative generation may be slower than analytics. |
| Teams timeout behavior | Power Automate flow limits should be considered. |
| Caching | Repeated review of the same package may benefit from cached analytics outputs. |

## 17. Scalability Plan

| Stage | Plan |
|---|---|
| MVP | Synchronous FastAPI processing for limited users. |
| Pilot | Add job IDs and background processing if reviews exceed acceptable response time. |
| Enterprise | Add queue-based processing, shared storage, centralized logging, and horizontal API scaling. |

## 18. Disaster Recovery

| Area | Recommendation |
|---|---|
| Code recovery | Source control with release tags. |
| Configuration recovery | Back up environment configuration and prompt versions. |
| Service recovery | Document restart procedures for FastAPI and Ollama. |
| Data recovery | Define whether review inputs and outputs are retained and backed up. |

## 19. Testing Strategy

### Unit Tests

| Target | Test Focus |
|---|---|
| `performance.py` | Metric correctness and edge cases. |
| `comparison.py` | Ranking and comparison consistency. |
| `drift.py` | Drift detection behavior. |
| `history.py` | Historical deviation and trend behavior. |
| `holiday.py` | Holiday risk and demand distortion logic. |
| `forecaster.py` | Forecaster ranking and consistency behavior. |
| `risk.py` | Risk scoring rules. |
| `insights.py` | Rule-based insight generation. |
| `recommendations.py` | Recommendation candidate logic. |

### Integration Tests

| Flow | Test Focus |
|---|---|
| API to analytics | Valid payload produces review package. |
| Analytics to LLM | Prompt context contains only verified outputs. |
| LLM to report | Narrative is included without changing metrics. |
| Power Automate to API | SharePoint file creation triggers API request correctly. |
| API to SharePoint output | Generated report and analytics outputs are written back to SharePoint. |

### UAT

User acceptance testing should involve forecast managers, regional forecast leads, analysts, and executive stakeholders. UAT should validate usefulness, clarity, trust, and actionability.

## 20. MVP Build Plan

### Phase 1

| Deliverable | Description |
|---|---|
| API skeleton | FastAPI project with health and version endpoints. |
| Request schema | Define and validate `POST /weekly-review` payload. |
| Dataset ingestion | Load uploaded Excel forecast file. |
| Dataset validation | Validate mandatory columns before analytics execution. |

### Phase 2

| Deliverable | Description |
|---|---|
| Analytics modules | Implement performance, comparison, drift, history, holiday, forecaster, risk, insights, and recommendations. |
| Review Engine | Build consolidated forecast review package. |
| Unit tests | Cover core analytics behavior. |

### Phase 3

| Deliverable | Description |
|---|---|
| Provider integration | Integrate Gemini and Company Provider models via `BaseLLMProvider`. |
| Master Prompt | Consolidate prompts into `MASTER_SUMMARY_PROMPT` outputting strict JSON. |
| Parsing logic | Implement `ResponseCleaner` and `ResponseParser`. |
| Resilience Layer | Implement `RetryPolicy` and `CircuitBreaker`. |

### Phase 4

| Deliverable | Description |
|---|---|
| Provider Chain | Failover routing from primary to secondary. |
| Report generators | Generate HTML, canonical JSON, and Markdown artifacts. |
| UAT | Validate with business users. |
| Pilot readiness | Add structured JSON metrics logging, error handling, and deployment documentation. |

## 21. Technical Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Incomplete input data | Review may be partial or inaccurate. | Validate inputs and expose limitations. |
| LLM output drift | Narrative quality may vary. | Version prompts and validate outputs. |
| Forecast scope creep | System may be treated as forecast generator. | Reinforce product definition and review boundaries. |
| Performance bottlenecks | Large data or LLM calls may slow responses. | Add async processing and queueing when needed. |
| Weak auditability | Results may be hard to defend. | Store versions, request IDs, and structured outputs. |

## 22. Technical Recommendations

1. Implement Python analytics modules before prompt tuning.
2. Define explicit health score and risk score rules with business stakeholders.
3. Treat prompt templates as versioned source artifacts.
4. Add validation around LLM outputs before sending responses to Teams.
5. Keep Copilot Studio outside the MVP unless a future business requirement justifies it.
6. Preserve Teams and Power Automate for the MVP user workflow.
7. Build test fixtures that represent realistic forecast, actuals, regional, and history data.
