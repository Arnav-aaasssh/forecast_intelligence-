---
name: dashboard-custom-1
description: Demand Forecast Dashboard Design Architect skill based on USM Supply Chain methodologies.
---

# Skill: Demand Forecast Dashboard Design Architect

## 1. Skill Overview
**Domain:** Supply Chain, Demand Planning, Business Intelligence (Power BI / Tableau)
**Source Methodology:** "7 Power BI Dashboards for Demand Planners" (USM Supply Chain)
**Purpose:** To guide the structural and visual design of demand forecast dashboards. This skill provides the exact specifications, chart types, and layout rules needed to build actionable dashboards that move planners away from static spreadsheets to dynamic, exception-based management.

---

## 2. Core Data Foundation (The Pre-Design Setup)
Before designing any visual, a specific relational data model must be assumed. Dashboards rely on this foundational structure:
* **SalesHistory Table:** `Date`, `SKU`, `Customer/Region`, `Actual Sales`
* **Forecast Table:** `Date`, `SKU`, `Customer/Region`, `Forecast Qty`
* **Calculated Metrics:** * `Error` = Forecast – Actual
    * `MAPE %` (Mean Absolute Percentage Error) = DIVIDE(ABS(Error), Actual)
    * `Bias` (Over/Under forecasting tendency)
* **Master Tables:** Calendar (Dates), Product Master (Lifecycle stage, category), Promo Master (Promo flags).

---

## 3. The 7 Types of Demand Planning Dashboards & Design Specs
When prompted to design a demand planning dashboard, select from or combine the following 7 standard archetypes. 

### Dashboard 1: Forecast Accuracy Tracker
* **Purpose:** To measure how far the forecast is from actual demand and whether the system is systematically over-forecasting or under-forecasting (Bias).
* **Primary Visual (Combo Chart):**
    * *X-Axis:* SKU or Product Family.
    * *Y-Axis 1 (Columns):* MAPE % (showing the magnitude of error).
    * *Y-Axis 2 (Line):* Bias % (showing the direction of error).
* **Design Note:** Use a prominent Card Visual at the top to display the aggregated total `Forecast Accuracy %` (1 - MAPE) for quick executive visibility.

### Dashboard 2: Demand Trend (Historical vs. Horizon)
* **Purpose:** To visualize sales trends over time, tracking seasonality and mapping the future forecast against historical actuals.
* **Primary Visual (Line Chart):**
    * *X-Axis:* Month/Week (Continuous Timeline).
    * *Y-Axis (Values):* Sum of Actual Sales (Solid Line) vs. Forecast Qty (Dashed Line).
* **Design Note:** Ensure the x-axis relies on a continuous Calendar table to avoid breaks in the trend line. Include YoY (Year-over-Year) comparison lines for deeper context.

### Dashboard 3: Promo & Event Lift Dashboard
* **Purpose:** To measure the true impact (lift) of promotional events by separating baseline sales from promotional spikes.
* **Primary Visual (Overlapped Column / Line Chart):**
    * *X-Axis:* Date / Promo Week.
    * *Y-Axis (Columns):* Stacked or clustered columns comparing `Baseline Sales` vs. `Promo Actuals`.
    * *Y-Axis (Line):* `Lift %` (Promo Sales – Baseline / Baseline).
* **Design Note:** Use distinct colors to differentiate "Promo" vs "Non-Promo" periods. 

### Dashboard 4: Customer / Channel Bias Tracker
* **Purpose:** To identify which specific customers, regions, or key accounts consistently over-order or under-order against forecasts.
* **Primary Visual (Column + Line Combo Chart):**
    * *X-Axis:* Customer Name / Channel.
    * *Y-Axis (Columns):* MAPE % by Customer.
    * *Y-Axis (Line):* Bias % by Customer.
* **Design Note:** Sort the visual in descending order of volume or MAPE to immediately highlight the most problematic accounts (e.g., Customer B always has a negative bias / over-orders).

### Dashboard 5: Product Lifecycle Matrix
* **Purpose:** To adapt forecast reviews based on product maturity. A new launch behaves differently than a phase-out product.
* **Primary Visual (Scatter or Bubble Chart):**
    * *X-Axis:* Product SKUs.
    * *Y-Axis:* Lifecycle Stage (Categorical: New Launch, Growth, Mature, Slow Mover, Phase-Out).
    * *Bubble Size:* Volume or Revenue contribution.
* **Design Note:** Grouping by lifecycle prevents planners from applying mature-product accuracy standards to highly volatile new launches.

### Dashboard 6: S&OP / Scenario Alignment Dashboard
* **Purpose:** Used for Sales & Operations Planning meetings to ensure the demand plan fits within supply capacity and financial goals.
* **Primary Visual (Waterfall Chart or Matrix):**
    * *Layout:* Compare Unconstrained Demand vs. Constrained Supply vs. Financial Target.
    * *KPI Cards:* Plan Attainment %, Rough-Cut Capacity limits.
* **Design Note:** This is an aggregated executive view. Avoid SKU-level clutter here; focus on Categories and Regions.

### Dashboard 7: The Daily Exception Dashboard (The "Where Do I Focus?" View)
* **Purpose:** A tactical, daily starting point for planners. It highlights immediate anomalies, low inventory coverage, and data quality issues so planners manage by exception rather than manually scanning spreadsheets.
* **Primary Visual (Scatter Chart Grid):**
    * *X-Axis:* Volume Deviation % (Actual vs typical demand/baseline).
    * *Y-Axis:* Coverage Days (On-Hand Inventory / Daily Forecast).
* **Design & Color Logic (CRITICAL):**
    * **Red:** Low coverage (< 7 days) = Immediate Stockout Risk.
    * **Orange:** High volume deviation (> ±30%) = Forecast needs urgent revision.
    * **Blue/Gray:** Clean SKUs (normal variance, healthy coverage).
    * **Data Labels:** Append an asterisk (*) to SKUs missing critical data inputs.

---

## 4. Global UI/UX Principles for Demand Dashboards
When generating design instructions for BI interfaces, the model must enforce these UI rules:

1.  **Top-Down Hierarchy:** * Top layer: High-level KPI cards (Total Accuracy, Global Bias, Total Lift).
    * Middle layer: Trend lines and bar charts (Context & Time).
    * Bottom layer: Granular tables or matrices (SKU-level detail for deep dives).
2.  **Universal Interactivity:** Every dashboard must feature accessible slicers/filters for:
    * `Date/Time Range`
    * `Region/Geography`
    * `Product Category/SKU`
3.  **Automated Empathy:** Never force the user to recalculate data visually. Calculate and display variances explicitly (e.g., instead of just showing Actual and Forecast, explicitly graph the `Variance` or `Error`).
4.  **Color Psychology:** * Actuals = Solid, dark colors (e.g., Deep Blue/Black).
    * Forecasts = Lighter, dashed, or outlined colors.
    * Alerts (Exceptions/Errors) = Semantic colors (Red/Orange).
