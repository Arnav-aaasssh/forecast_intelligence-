# Forecast Review & Decision Support System

## System Design Document

## Document Purpose

This document defines the business and solution design for the Forecast Review & Decision Support System. It is intended for executives, product owners, solution architects, delivery leads, forecast managers, analysts, and implementation teams.

The design reflects the current approved direction:

| Area | Decision |
|---|---|
| Product type | Forecast review and decision support platform |
| Primary interface | Microsoft Teams |
| MVP storage | SharePoint |
| Workflow orchestration | Power Automate |
| Backend | FastAPI |
| Analytics | Deterministic Python modules |
| LLM role | Provider-agnostic narrative generation via ProviderChain |
| Core principle | Python = Truth; LLM = Narrative |

## 1. Executive Summary

### Business Problem

Forecast-dependent teams need a consistent way to evaluate the quality, reliability, and business risk of existing forecasts before management decisions are made. Forecast outputs may come from different teams, regions, tools, or statistical approaches, which can make it difficult to determine whether a forecast is accurate, stable, explainable, and suitable for executive use.

The organization needs a governance-oriented review process that can:

| Need | Description |
|---|---|
| Forecast validation | Determine whether an existing forecast is reliable enough to support decisions. |
| Risk visibility | Identify forecast degradation, drift, volatility, and regional concerns. |
| Approach comparison | Compare available forecasting approaches using objective analytics. |
| Management insight | Convert technical review outputs into concise executive narratives. |
| Decision support | Provide recommended actions through Microsoft Teams. |

### Solution Overview

The Forecast Review & Decision Support System evaluates existing forecast datasets using a Python analytics layer, produces structured review outputs, and uses a provider-agnostic LLM chain to create narrative summaries, explanations, and recommendations. Users upload forecast files through Microsoft Teams. The files are stored in SharePoint, detected by Power Automate, processed by a FastAPI backend, reviewed by deterministic analytics modules, summarized by the ProviderChain (strict JSON), parsed, and returned to Teams as a management-ready report.

The core design principle is:

> Python = Truth  
> LLM = Narrative

Python performs all calculations, metrics, scoring, comparisons, and risk logic. The LLM receives verified analytics outputs and transforms them into clear language for executives, forecast managers, regional leads, and analysts.

The system evaluates:

| Evaluation Area | Description |
|---|---|
| Forecast quality | Determines whether forecast outputs are reliable enough for decision support. |
| Forecast accuracy | Compares manual and ML forecasts against actuals. |
| Forecast drift | Detects changes between previous and current forecasts. |
| Historical consistency | Reviews current behavior against historical patterns. |
| Forecast risk | Produces risk score, category, drivers, and ranking. |
| Forecast stability | Evaluates volatility and abnormal movement. |

### Expected Business Value

| Value Area | Expected Benefit |
|---|---|
| Governance | Standardized review process for forecasts across regions and teams. |
| Decision quality | Management decisions are supported by objective forecast health and risk evidence. |
| Speed | Forecast review packages can be generated faster than manual analysis cycles. |
| Consistency | Forecasts are assessed using repeatable metrics and review logic. |
| Transparency | Recommendations are traceable to Python-generated analytics. |
| Adoption | Microsoft Teams provides a familiar interface for business users. |

## 2. Product Vision

### Purpose

The system provides a formal review and decision support capability for existing forecasts. It helps business and forecasting teams understand whether a forecast should be trusted, challenged, adjusted, escalated, or monitored.

### Scope

The product scope includes:

| In Scope | Description |
|---|---|
| Forecast review | Evaluate existing forecast data and related actuals. |
| Forecast governance | Apply consistent review criteria and risk interpretation. |
| Decision support | Provide recommendations based on analytics outputs. |
| Management narrative | Generate executive-ready explanations using an LLM. |
| Teams delivery | Accept requests and return responses through Microsoft Teams. |
| SharePoint storage | Store uploaded files, analytics results, reports, and audit logs for the MVP. |

The product scope excludes:

| Out of Scope | Description |
|---|---|
| Forecast generation as primary function | The system is not intended to be a forecasting engine. |
| LLM-based calculations | The LLM must not calculate metrics, scores, or accuracy values. |
| Unverified recommendations | Recommendations must be grounded in analytics outputs. |
| Replacement of source planning systems | The system reviews forecast data; it does not become the planning system of record. |
| Database-backed governance in MVP | MVP storage is SharePoint; SQL Server or PostgreSQL is future scope. |

### Objectives

1. Provide a repeatable forecast review process.
2. Quantify forecast performance, risk, drift, and comparison results.
3. Generate a forecast review package suitable for management consumption.
4. Deliver actionable recommendations through Microsoft Teams.
5. Maintain clear separation between deterministic analytics and generative narrative.

### Success Criteria

| Criterion | Measure |
|---|---|
| Accuracy of review logic | Metrics and scores are produced by tested Python modules. |
| Explainability | Every narrative statement can be traced to supplied analytics context. |
| Usability | Users can request and receive reviews from Teams. |
| Consistency | Similar inputs produce consistent review outputs. |
| Maintainability | Analytics modules, review logic, prompts, and reports are separately managed. |

## 3. Product Definition

### What This System Is Not

This system is not a forecasting engine. It does not replace statistical forecasting tools, demand planning tools, enterprise planning platforms, or human forecasting workflows. It does not create official forecasts as its primary responsibility.

### What This System Is

| Product Identity | Meaning |
|---|---|
| Forecast Review System | Reviews existing forecasts against actuals, history, and risk indicators. |
| Forecast Governance Platform | Applies a consistent framework for assessing forecast health and management readiness. |
| Decision Support System | Converts reviewed analytics into recommendations and executive narratives. |

The system may include a `forecaster.py` module for controlled comparison or benchmark purposes, but forecast generation is not the primary product purpose.

## 4. User Personas

### Forecast Manager

| Attribute | Description |
|---|---|
| Primary goal | Understand whether a forecast is reliable and defensible. |
| Typical questions | Is the forecast accurate? What risks should I escalate? What action should we take? |
| Needs | Forecast health score, risk explanation, comparison results, recommendations. |

### Regional Forecast Lead

| Attribute | Description |
|---|---|
| Primary goal | Understand regional forecast performance and local risk drivers. |
| Typical questions | Which regions have drift? Which region needs intervention? |
| Needs | Regional insights, holiday impact awareness, drift analysis, localized recommendations. |

### Executive Stakeholder

| Attribute | Description |
|---|---|
| Primary goal | Make business decisions with confidence. |
| Typical questions | Can I trust this forecast? What is the risk? What decision is recommended? |
| Needs | Executive summary, health score, risk level, plain-language recommendations. |

### Analyst

| Attribute | Description |
|---|---|
| Primary goal | Validate results, inspect metrics, and improve review quality. |
| Typical questions | What metrics drove the score? Which module produced this finding? |
| Needs | Detailed analytics outputs, module-level results, reproducible logic. |

## 5. End-to-End Workflow

The MVP workflow is file-driven and Teams-first:

| Step | Component | Action |
|---|---|---|
| 1 | Microsoft Teams | User uploads a forecast file, such as `Forecast_Week_32.xlsx`. |
| 2 | SharePoint | File is stored in `ForecastReview/InputFiles/`. |
| 3 | Power Automate | Flow detects file creation using a "When file is created" trigger. |
| 4 | Power Automate | Flow retrieves file content from SharePoint. |
| 5 | Power Automate | Flow invokes FastAPI using `POST /weekly-review`. |
| 6 | FastAPI | API validates the request and loads the dataset. |
| 7 | Forecast Review Engine | Engine executes analytics modules in sequence. |
| 8 | Analytics Engine | Python modules calculate accuracy, comparison, drift, history, holiday impact, risk, insights, and recommendations. |
| 9 | Forecast Review Engine | Engine consolidates module outputs into a structured analytics package. |
| 10 | LLM Layer | ProviderChain converts structured findings into a strict JSON SummaryBundle. |
| 11 | Report Generation Layer | Markdown, HTML, and JSON packages are generated from the SummaryBundle. |
| 12 | SharePoint | Reports, analytics results, and audit logs are written back to SharePoint. |
| 13 | Power Automate | Flow posts completion notification and summary back to Teams. |

## 6. Functional Components

### Teams Interface

Microsoft Teams acts as the user-facing entry point. It supports forecast file upload, result notification, and user access to the generated review package without requiring a separate custom frontend for the MVP.

| Responsibility | Description |
|---|---|
| File upload | Allow users to upload weekly forecast datasets. |
| Response display | Present the executive summary, recommendations, and report link. |
| Adoption channel | Use an existing business collaboration platform. |
| Follow-up entry point | Support future routed questions against reviewed outputs. |

Teams performs no calculations and does not host business logic.

### SharePoint Storage Layer

SharePoint is the MVP storage layer and document repository.

| Folder | Purpose |
|---|---|
| `ForecastReview/InputFiles/` | Uploaded forecast files. |
| `ForecastReview/AnalyticsResults/` | Structured analytics outputs from Python. |
| `ForecastReview/Reports/` | Generated Forecast Review Packages. |
| `ForecastReview/AuditLogs/` | Processing records, request IDs, and traceability logs. |

### Power Automate Layer

Power Automate acts as the workflow orchestrator between Teams and FastAPI.

| Responsibility | Description |
|---|---|
| Trigger handling | Detect forecast file creation in SharePoint. |
| File retrieval | Retrieve uploaded file content. |
| API invocation | Call `POST /weekly-review` on the FastAPI backend. |
| Result storage | Store reports and analytics results in SharePoint. |
| Response routing | Post the completed result and report link back into Teams. |

### FastAPI Layer

FastAPI provides the backend API boundary.

| Responsibility | Description |
|---|---|
| Request validation | Validate file, metadata, and required dataset fields. |
| Workflow coordination | Invoke analytics, review, LLM, and report layers. |
| Response management | Return structured review outputs. |
| Health monitoring | Expose health and version endpoints. |

Primary MVP endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /weekly-review` | Process the uploaded forecast file and generate the Forecast Review Package. |
| `POST /ask-question` | Support follow-up questions against reviewed outputs where enabled. |
| `GET /health` | Confirm service availability. |

### Analytics Engine

The Analytics Engine is the source of truth. It performs deterministic calculations and produces structured outputs.

| Module | Purpose |
|---|---|
| `performance.py` | Calculates forecast accuracy and performance metrics. |
| `comparison.py` | Compares existing forecast approaches or forecast versions. |
| `drift.py` | Detects drift between forecast behavior and actual or historical patterns. |
| `history.py` | Analyzes historical trends and prior performance. |
| `holiday.py` | Identifies holiday or calendar-related context that may affect interpretation. |
| `forecaster.py` | Evaluates forecaster performance and consistency. |
| `risk.py` | Converts analytics outputs into structured risk indicators and risk score inputs. |
| `insights.py` | Produces deterministic business insight candidates from analytics outputs. |
| `recommendations.py` | Generates rule-based recommendation candidates from verified analytics. |

### Forecast Review Engine

The Forecast Review Engine consolidates analytics outputs into a coherent review package. It does not perform free-form reasoning. Its role is to organize structured facts, scores, risks, insights, and recommendation candidates for downstream reporting and narrative generation.

### LLM Layer

The LLM layer utilizes a `ProviderChain` to route a unified `MASTER_SUMMARY_PROMPT` to a primary LLM (e.g., Gemini) with automatic failover to a secondary LLM. The LLM creates narrative text strictly constrained to a `SummaryBundle` JSON schema. It must not calculate, infer missing metrics, fabricate business context, or override Python analytics.

| Allowed | Not Allowed |
|---|---|
| Summaries | Accuracy calculations |
| Explanations | Risk scoring |
| Recommendations based on supplied facts | Forecast metric computation |
| Executive narratives | Unverified assumptions |

### Report Generation Layer

The Report Generation Layer produces the final forecast review package as deterministic HTML, JSON, and Markdown artifacts generated purely from the `SummaryBundle`.

## 7. Dataset Requirements

The MVP depends on a standard forecast dataset structure. Files are expected to be uploaded through Teams and stored in SharePoint before processing.

### Mandatory Fields

| Field | Purpose |
|---|---|
| `Forecast_Name` | Identifies the forecast set. |
| `Fiscal_Year` | Fiscal year context. |
| `Fiscal_Week` | Fiscal week context. |
| `Region` | Regional grouping. |
| `Country` | Country grouping. |
| `Offering` | Product or service offering. |
| `Channel` | Channel grouping. |
| `Forecaster` | Forecast owner or forecaster identifier. |
| `Manual_Forecast` | Manual forecast value. |
| `ML_Forecast` | Machine learning forecast value. |
| `Previous_Forecast` | Prior forecast value for drift analysis. |
| `Actual_Offered` | Actual observed value. |
| `Holiday_Count` | Holiday count or holiday impact indicator. |
| `Risk_Flag` | Existing risk flag if supplied. |
| `Risk_Category` | Existing risk category if supplied. |
| `Mean (Hist Contacts)` | Historical mean for volatility analysis. |
| `Std Dev (Hist Contacts)` | Historical standard deviation for volatility analysis. |

Where available, `Final_Y1`, `Final_Y2`, `Final_Y3`, `Final_Y4`, and `Final_Y5` support historical trend and abnormal forecast detection.

## 8. Risk Scoring Framework

Risk scoring is calculated by Python and must remain auditable.

| Risk Component | Source Logic |
|---|---|
| Accuracy Risk | `100 - Accuracy` |
| Drift Risk | Forecast revision percentage between current and previous forecast |
| Volatility Risk | Coefficient of variation: `Std Dev / Historical Mean` |
| Holiday Risk | Derived from `Holiday_Count` |

### Drift Threshold Example

| Drift Range | Risk Level |
|---|---|
| 0-5% | Low |
| 5-10% | Medium |
| 10-15% | Elevated |
| 15%+ | High |

### Final Risk Score Weighting

| Component | Weight |
|---|---|
| Accuracy Risk | 40% |
| Drift Risk | 20% |
| Volatility Risk | 20% |
| Holiday Risk | 20% |

## 9. Forecast Review Package

The forecast review package contains the following sections:

| Section | Description |
|---|---|
| Executive Summary | Concise management-level interpretation of the review. |
| Forecast Health Score | Overall health assessment produced from Python-generated indicators. |
| Risk Assessment | Key risk factors, severity, and rationale. |
| Forecast Comparison | Comparison across available forecast approaches or versions. |
| Drift Analysis | Evidence of drift, instability, or changing forecast behavior. |
| Historical Analysis | Historical deviation, trend direction, and abnormal forecast detection. |
| Regional Insights | Region-level findings where regional data is provided. |
| Root Cause Analysis | Rule-based explanation of likely drivers using supplied data. |
| Recommendation Section | Recommended actions grounded in analytics outputs. |
| Management Actions | Follow-up actions and escalation notes. |

## 10. Architecture View

### Plain-Text Architecture Flow

```text
Business User
  -> Microsoft Teams
  -> SharePoint InputFiles folder
  -> Power Automate
  -> FastAPI backend
  -> Forecast Review Engine
  -> Python Analytics Modules
  -> Consolidated Analytics Package
  -> ProviderChain (Gemini -> Failover)
  -> JSON SummaryBundle Validation
  -> Report Generation Layer
  -> SharePoint Reports, AnalyticsResults, and AuditLogs folders
  -> Microsoft Teams response
```

### Component Interaction Summary

| Source | Target | Interaction |
|---|---|---|
| Microsoft Teams | SharePoint | User uploads the forecast file through Teams and the file is stored in SharePoint. |
| SharePoint | Power Automate | File creation triggers the automation flow. |
| Power Automate | FastAPI | Flow sends file content to the review endpoint. |
| FastAPI | Forecast Review Engine | API validates the request and starts review processing. |
| Forecast Review Engine | Analytics modules | Engine executes deterministic Python modules. |
| Analytics modules | Forecast Review Engine | Modules return structured metrics, risks, insights, and recommendations. |
| Forecast Review Engine | ProviderChain | Engine sends structured findings injected into `MASTER_SUMMARY_PROMPT`. |
| ProviderChain | Report Generation Layer | LLM returns strict JSON parsed into a `SummaryBundle`. |
| Report Generation Layer | SharePoint | HTML, JSON, and Markdown artifacts are generated and stored. |
| Power Automate | Microsoft Teams | Teams receives the completion message and review summary. |

## 11. MVP Scope

| MVP Capability | Description |
|---|---|
| Teams upload | Upload a forecast file from Teams. |
| SharePoint storage | Store input files, reports, analytics results, and audit logs. |
| Power Automate orchestration | Detect file creation, call FastAPI, store results, and notify Teams. |
| FastAPI review endpoint | Provide `POST /weekly-review`. |
| Python analytics modules | Implement deterministic review logic. |
| Forecast Review Engine | Assemble structured review package. |
| ProviderChain LLM Layer | Generate JSON management summaries via Gemini/Company fallback. |
| Report Output | Generate HTML, JSON, and Markdown artifacts and store in SharePoint. |
| Teams response | Return a concise review summary, recommendations, and report location. |

## 12. Performance Targets

| Process Area | Target |
|---|---|
| Dataset validation | Less than 30 seconds |
| Analytics processing | Less than 3 minutes |
| Report generation | Less than 5 minutes |
| LLM summary | Less than 30 seconds |
| Follow-up questions | Less than 15 seconds |

## 13. Future Roadmap

| Horizon | Capability |
|---|---|
| Near term | Build dataset ingestion, analytics modules, review engine, ProviderChain LLM integration, Markdown/HTML generation, and Power Automate integration. |
| Medium term | Add risk trend tracking, multi-week forecast comparison, forecast approval workflows, and automated escalations. |
| Long term | Add governance dashboard, interactive forecast assistant, scenario analysis, SQL Server or PostgreSQL storage, and enterprise deployment patterns. |

## 14. Final Design Statement

The Forecast Review & Decision Support System is an automated forecast review and governance platform. It does not generate forecasts. It evaluates existing forecast datasets, applies deterministic analytics, produces a structured Forecast Review Package, and communicates the results through Microsoft Teams.

Python determines the truth. The LLM communicates the truth.
