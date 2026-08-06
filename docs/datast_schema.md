# dataset_schema.md

# Forecast Review & Decision Support System

## Dataset Schema & Data Contract

---

# 1. Purpose

This document defines the structure, meaning, validation rules, and analytical usage of the Forecast Review dataset.

It acts as the single source of truth for all analytics modules within the Forecast Review & Decision Support System.

Every analytics module must reference this document before consuming dataset fields.

---

# 2. Dataset Overview

## Dataset Name

Forecast Review Dataset

## Source

Forecast Planning Team

## File Format

Excel (.xlsx)

## Update Frequency

Weekly

## Grain

One row represents a single forecast record for a specific:

* Forecast
* Fiscal Week
* Geography
* Offering
* Channel
* Forecaster

---

# 3. Dataset Pipeline

Forecast Analyst

↓

Exports Forecast Dataset

↓

Uploads Excel File to Teams

↓

Teams stores file in SharePoint

↓

Power Automate retrieves file

↓

FastAPI receives dataset

↓

Validation Layer

↓

Forecast Review Engine

↓

Analytics Modules

↓

ProviderChain (LLM Execution)

↓

ResponseParser (JSON Validation)

↓

Forecast Review Package (Markdown, HTML, JSON)

---

# 4. Column Definitions

| Column                             | Data Type | Required | Description                      | Used By                       |
| ---------------------------------- | --------- | -------- | -------------------------------- | ----------------------------- |
| Forecast_Name                      | String    | Yes      | Forecast identifier              | Metadata                      |
| Model                              | String    | Yes      | Forecast model                   | Metadata                      |
| Family                             | String    | Yes      | Forecast family                  | Metadata                      |
| Fiscal_Year                        | Integer   | Yes      | Fiscal year                      | Reporting                     |
| Week_Ending                        | Date      | Yes      | Forecast week end date           | Reporting                     |
| Fiscal_Week                        | Integer   | Yes      | Fiscal week number               | Reporting                     |
| Month_Number                       | Integer   | Yes      | Month index                      | Reporting                     |
| Week_Number                        | Integer   | Yes      | Week index                       | Reporting                     |
| Country                            | String    | Yes      | Country                          | Segmentation                  |
| Region                             | String    | Yes      | Region                           | Segmentation                  |
| SubRegion                          | String    | Yes      | Sub-region                       | Segmentation                  |
| Offering                           | String    | Yes      | Product/Service offering         | Segmentation                  |
| Channel                            | String    | Yes      | Business channel                 | Segmentation                  |
| Forecaster                         | String    | Yes      | Forecast owner                   | forecaster.py                 |
| Planned_ASU                        | Float     | Yes      | Planned ASU                      | Reference                     |
| Actual_ASU                         | Float     | Yes      | Actual ASU                       | Reference                     |
| Final_Units                        | Float     | Yes      | Final units                      | Reference                     |
| Final_Y1–Final_Y5                  | Float     | Yes      | Historical values                | history.py                    |
| Final_upp_units                    | Float     | Yes      | Upper planning units             | Reference                     |
| Holiday_Count                      | Integer   | Yes      | Number of holidays               | holiday.py                    |
| Monday–Sunday                      | Integer   | Yes      | Daily distribution               | Future analytics              |
| Volume_Category                    | String    | Yes      | Volume classification            | Segmentation                  |
| Manual_Adh                         | Float     | Yes      | Manual adherence                 | performance.py                |
| ML_Adh                             | Float     | Yes      | ML adherence                     | comparison.py                 |
| Manual_±10%                        | Boolean   | Yes      | Manual forecast within tolerance | performance.py                |
| ML_±10%                            | Boolean   | Yes      | ML forecast within tolerance     | comparison.py                 |
| ML≥Manual_or_±10%                  | Boolean   | Yes      | ML comparison flag               | comparison.py                 |
| Mean (Hist. Contacts) (Last 1 yr.) | Float     | Yes      | Historical mean                  | history.py                    |
| Std Dev (Hist. Contacts)           | Float     | Yes      | Historical deviation             | history.py, risk.py           |
| RISK Cat (w/ Holiday)              | String    | Yes      | Existing business risk category  | risk.py                       |
| RISK Flag (w/ Holiday)             | String    | Yes      | Existing business risk flag      | risk.py                       |
| Actual_Offered                     | Float     | Yes      | Actual observed demand           | performance.py                |
| Manual_Forecast                    | Float     | Yes      | Manual forecast                  | performance.py                |
| Previous_Forecast                  | Float     | Yes      | Previous forecast                | drift.py                      |
| ML_Forecast                        | Float     | Yes      | ML forecast                      | performance.py, comparison.py |

---

# 5. Module Dependencies

## performance.py

Consumes:

* Manual_Forecast
* ML_Forecast
* Actual_Offered

Produces:

* Manual Accuracy
* ML Accuracy
* Forecast Error
* Health Score

---

## comparison.py

Consumes:

* Manual_Forecast
* ML_Forecast
* Actual_Offered
* Manual_Adh
* ML_Adh

Produces:

* ML vs Manual Comparison
* Win Rate
* Performance Difference

---

## drift.py

Consumes:

* Previous_Forecast
* Manual_Forecast
* ML_Forecast

Produces:

* Forecast Drift
* Revision %
* Drift Direction

---

## history.py

Consumes:

* Final_Y1
* Final_Y2
* Final_Y3
* Final_Y4
* Final_Y5
* Mean (Hist. Contacts) (Last 1 yr.)
* Std Dev (Hist. Contacts)

Produces:

* Historical Deviation
* Trend
* Volatility

---

## holiday.py

Consumes:

* Holiday_Count
* Monday–Sunday

Produces:

* Holiday Impact
* Seasonality Indicators

---

## forecaster.py

Consumes:

* Forecaster
* Manual_Adh
* ML_Adh

Produces:

* Forecaster Rankings
* Consistency Scores

---

## risk.py

Consumes:

Outputs from:

* performance.py
* drift.py
* history.py
* holiday.py

Plus:

* RISK Cat (w/ Holiday)
* RISK Flag (w/ Holiday)

Produces:

* Risk Score
* Risk Category
* Risk Drivers

---

## insights.py

Consumes outputs from all analytics modules.

Produces business observations.

---

## recommendations.py

Consumes outputs from:

* insights.py
* risk.py

Produces management recommendations.

---

# 6. Validation Rules

* Required columns must exist.
* Numeric fields must contain numeric values.
* Forecast values cannot be negative.
* Holiday_Count must be ≥ 0.
* Fiscal_Week must be between 1 and 53.
* Month_Number must be between 1 and 12.
* Region, Offering, Channel, and Forecaster cannot be empty.

---

# 7. Missing Value Strategy

| Field             | Strategy       |
| ----------------- | -------------- |
| Actual_Offered    | Reject dataset |
| Manual_Forecast   | Reject dataset |
| ML_Forecast       | Reject dataset |
| Previous_Forecast | Reject row     |
| Holiday_Count     | Replace with 0 |
| Historical Mean   | Reject row     |
| Std Dev           | Reject row     |

---

# 8. Derived Metrics

Forecast Accuracy

Accuracy = 1 − |Forecast − Actual| / Actual

Forecast Error

Forecast − Actual

Forecast Drift

(Current Forecast − Previous Forecast) / Previous Forecast

Coefficient of Variation

Std Dev / Historical Mean

Risk Score

40% Accuracy Risk

20% Drift Risk

20% Volatility Risk

20% Holiday Impact

---

# 9. Output Contract

Every analytics module must return structured JSON-compatible outputs.

No module should directly generate reports or natural-language summaries.

Only the LLM layer is responsible for narrative generation.

---

# 10. Design Principle

The dataset is the single source of truth.

Python performs all calculations.

LLM communicates analytical findings.

No business metric is calculated by the LLM.
