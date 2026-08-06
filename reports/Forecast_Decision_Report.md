# FORECAST DECISION DASHBOARD

────────────────────────

FORECAST DECISION

[Pilot Deployment]

Confidence

LOW

Business Risk

LOW

Deployment Strategy

GLOBAL

Recommended Model

V2_9_Prophet

Next Action

Pilot for 4 weeks before enterprise rollout.

────────────────────────

| Best WAPE | Weekly Win Rate | Volume CV | Models Evaluated |
|---|---|---|---|
| 9.47% | 51.52% | 7.59% | 92 |

**Executive Takeaway**

Machine Learning currently ranks first, however statistical evidence is insufficient to justify immediate production rollout.

**Key Evidence**

• Proposed model achieves 9.47% WAPE.
• No incumbent baseline is available for comparative evaluation (Greenfield).
• Model V2_9_Prophet ranked #1 out of 92 candidates.
• Volume remains stable (CV: 7.59%), creating a favorable forecasting environment.



---

## Accuracy Assessment (Incumbent vs ML)

> **Business Question:** Did human planners or machine learning algorithms produce more accurate forecasts?

**Observation:** No incumbent baseline is available for comparison (Greenfield scenario).
**Evidence:** Baseline Availability: False
**Conclusion:** No incumbent baseline is available for comparison (Greenfield).
**Decision Support:** The ML model establishes the initial operational baseline for future comparison.


---

## Model Champion Selection

> **Business Question:** Which forecasting model ranked first across all evaluated candidates?

**Observation:** Model V2_9_Prophet ranked #1 across 92 scored candidates with a composite score of 75.32/100. It leads V3_33_Prophet by 7.22 points.

**Primary Evidence:**
- **Winsorized Composite Score:** 75.32/100
- **WAPE:** 9.47%
- **Weekly Win Rate:** 51.52%

**Supporting Evidence:**
- **Absolute Bias:** 0.83%
- **IQR Stability:** 13.85%
- **Hit10 Rate:** 65.66%
- **Runner-up Composite Score:** 68.09/100
- **Total Models Scored:** 92

**Conclusion:** Model V2_9_Prophet achieved the highest composite score across all evaluated candidates.

**Decision Support:** If confidence is Low, the champion ranking is reported for informational purposes only.


*(Chart Placeholder: [horizontal_bar_chart] Model Composite Scores - Ranking of all evaluated models based on Winsorized Composite Score.)*

*Appendix A: Full Model Scorecard Breakdown*

---

## Business Context (Actuals)


**Charts**

![Weekly Volume Trend](D:/project_1 imp docs/Forecast review/reports/charts/volume_trend.png)

> **Business Question:** Was the underlying demand volume stable enough to be forecasted?

**Observation:** Demand variability remained low (CV 7.59%). 3 statistical anomalies were detected (Z > 2.5). Overall volume exhibits a Flat trend.

**Primary Evidence:**
- **Coefficient of Variation:** 7.59%
- **Anomaly Count:** 3
- **Trend Direction:** Flat

**Supporting Evidence:**
- **Mean Volume:** 188,435

**Conclusion:** Demand remained statistically stable throughout the evaluation period.

**Decision Support:** Volume conditions should be considered favorable when reviewing forecast accuracy results.



---

## Forecast Degradation Analysis

> **Business Question:** Did unexpected volume spikes or drops cause the forecast to fail?

**Observation:** Detected 3 volume anomalies, but none coincided with severe forecast degradation.

**Primary Evidence:**
- **Total Anomalies:** 3
- **Severe Degradation Events:** 0

**Conclusion:** The champion model successfully maintained accuracy despite anomalous volume events.

**Decision Support:** The evaluated model demonstrated resilience against external volume shocks.


*Appendix B: Detailed Event Timeline*

---

## Appendix A: Statistical & Data Audit

> **Business Question:** What are the underlying statistical proofs for this document?

**Conclusion:** See attached tables for full statistical, normalization, and exclusion audit.


| Model | Composite Score | WAPE | Abs Bias | Stability IQR | Hit10 |
| --- | --- | --- | --- | --- | --- |
| V2_9_Prophet | 75.32 | 9.47% | 0.83% | 13.85% | 65.66% |
| V3_33_Prophet | 68.09 | 10.34% | 2.73% | 16.11% | 58.59% |
| V2_2_ARIMA | 67.56 | 11.57% | 2.96% | 15.35% | 59.60% |
| V2_4_Prophet | 62.73 | 11.81% | 3.85% | 17.76% | 54.55% |
| V2_37_Prophet | 60.55 | 9.50% | 3.92% | 20.80% | 48.82% |
| V2_38_Prophet | 57.67 | 11.05% | 0.37% | 25.40% | 44.44% |
| V3_38_Prophet | 56.53 | 13.02% | 1.78% | 21.61% | 43.77% |
| V3_22_Prophet | 55.80 | 14.46% | 1.16% | 21.89% | 44.44% |
| V3_0_LR_With_VIF | 55.65 | 12.15% | 7.46% | 18.65% | 48.48% |
| V2_32_Prophet | 53.06 | 15.67% | 3.12% | 21.88% | 45.45% |
| V3_15_Prophet | 51.95 | 13.79% | 2.78% | 25.30% | 42.93% |
| V3_3_ARIMA | 51.20 | 12.45% | 3.70% | 26.11% | 41.41% |
| V2_40_Prophet | 49.29 | 13.76% | 6.36% | 23.03% | 41.41% |
| V3_37_Prophet | 46.99 | 16.87% | 5.28% | 23.73% | 41.92% |
| V3_48_Prophet | 46.24 | 15.75% | 9.39% | 22.59% | 45.45% |
| V2_47_Prophet | 45.68 | 17.80% | 0.01% | 34.05% | 38.38% |
| V3_9_Prophet | 45.50 | 16.58% | 1.37% | 28.49% | 35.86% |
| V2_22_Prophet | 45.34 | 17.33% | 4.90% | 26.40% | 42.42% |
| V2_13_Prophet | 44.51 | 19.72% | 1.24% | 27.04% | 38.38% |
| V3_46_Prophet | 44.38 | 15.91% | 2.56% | 34.50% | 36.87% |
| V3_19_Prophet | 43.84 | 18.31% | 0.22% | 30.64% | 35.69% |
| V3_40_Prophet | 43.46 | 19.21% | 2.07% | 28.13% | 38.38% |
| V3_25_Prophet | 42.88 | 15.61% | 4.93% | 28.54% | 35.86% |
| V3_27_Prophet | 41.94 | 15.37% | 4.92% | 32.96% | 35.35% |
| V2_29_Prophet | 41.57 | 15.83% | 9.92% | 23.64% | 37.37% |
| V2_43_Prophet | 41.27 | 18.84% | 2.12% | 34.48% | 35.35% |
| V3_6_Prophet | 41.24 | 17.15% | 6.76% | 26.96% | 37.49% |
| V3_20_Prophet | 40.86 | 14.54% | 5.84% | 34.01% | 33.00% |
| V3_8_Prophet | 40.82 | 16.00% | 8.35% | 58.01% | 42.42% |
| V3_44_Prophet | 40.81 | 13.78% | 10.87% | 24.23% | 33.84% |
| V3_0_XGB | 40.22 | 16.06% | 5.11% | 31.37% | 33.33% |
| V3_1_Prophet | 40.12 | 15.87% | 6.76% | 26.70% | 31.31% |
| V3_11_Prophet | 39.48 | 18.67% | 6.85% | 28.58% | 39.73% |
| V2_6_Prophet | 38.88 | 17.93% | 3.19% | 58.93% | 26.60% |
| V3_43_Prophet | 38.60 | 15.49% | 8.00% | 41.19% | 35.02% |
| V3_0_Prophet | 38.13 | 21.18% | 0.75% | 38.75% | 30.14% |
| V3_35_Prophet | 37.36 | 21.79% | 9.91% | 28.60% | 49.49% |
| V3_4_Prophet | 36.98 | 18.54% | 5.77% | 34.33% | 33.11% |
| V2_11_Prophet | 36.67 | 14.85% | 13.63% | 27.51% | 38.38% |
| V2_28_Prophet | 36.64 | 18.29% | 5.83% | 40.11% | 31.82% |
| V3_7_Prophet | 36.53 | 20.33% | 3.14% | 44.62% | 24.82% |
| V3_0_ARIMA | 36.43 | 18.43% | 5.14% | 41.96% | 25.38% |
| V3_10_Prophet | 35.96 | 19.08% | 6.35% | 32.13% | 33.33% |
| V3_32_Prophet | 35.58 | 17.86% | 10.60% | 26.66% | 34.34% |
| V2_24_Prophet | 34.88 | 25.31% | 0.78% | 42.70% | 32.32% |
| V3_31_Prophet | 34.20 | 22.74% | 3.05% | 39.95% | 26.26% |
| V3_34_Prophet | 33.16 | 22.35% | 4.69% | 34.44% | 30.51% |
| V2_44_Prophet | 33.09 | 22.92% | 3.98% | 38.22% | 26.77% |
| V3_16_Prophet | 32.38 | 22.44% | 5.18% | 35.34% | 27.44% |
| V3_1_ARIMA | 31.97 | 18.16% | 14.67% | 28.20% | 38.64% |
| V3_17_Prophet | 31.08 | 23.34% | 5.59% | 43.11% | 25.25% |
| V2_0_ARIMA | 30.77 | 17.93% | 11.29% | 52.88% | 26.77% |
| V3_12_Prophet | 30.48 | 20.58% | 9.38% | 32.63% | 31.06% |
| V3_18_Prophet | 29.96 | 26.96% | 3.08% | 43.46% | 26.77% |
| V3_10_XGB | 28.33 | 30.10% | 1.57% | 59.38% | 22.22% |
| V3_23_Prophet | 25.58 | 24.78% | 9.64% | 40.12% | 25.93% |
| V4_0_LR_With_VIF | 24.87 | 25.03% | 10.10% | 45.33% | 26.60% |
| V3_4_ARIMA | 24.45 | 26.68% | 8.86% | 52.85% | 21.34% |
| V3_13_Prophet | 24.43 | 29.37% | 6.19% | 44.79% | 25.05% |
| V2_10_Prophet | 24.14 | 23.57% | 15.58% | 31.41% | 37.88% |
| V4_10_XGB | 23.20 | 34.52% | 2.29% | 46.77% | 24.24% |
| V4_11_XGB | 22.96 | 26.65% | 10.39% | 43.63% | 28.28% |
| V3_14_Prophet | 22.90 | 30.89% | 6.21% | 47.30% | 17.17% |
| V4_2_ARIMA | 22.69 | 30.36% | 6.94% | 48.65% | 14.14% |
| V2_23_Prophet | 21.13 | 24.73% | 14.13% | 37.52% | 28.28% |
| V3_30_Prophet | 20.34 | 28.71% | 10.96% | 52.14% | 22.22% |
| V2_46_Prophet | 17.73 | 23.55% | 21.68% | 28.09% | 27.27% |
| V4_0_ARIMA | 17.55 | 51.20% | 2.45% | 90.99% | 20.20% |
| V3_2_ARIMA | 17.52 | 27.23% | 15.25% | 45.94% | 26.46% |
| V2_0_LR_With_VIF | 16.94 | 30.22% | 12.84% | 52.16% | 20.54% |
| V4_6_XGB | 15.39 | 61.33% | 4.61% | 72.75% | 18.18% |
| V3_21_Prophet | 14.88 | 35.67% | 9.45% | 79.68% | 18.86% |
| V3_24_Prophet | 14.06 | 28.23% | 17.71% | 36.51% | 22.22% |
| V3_28_Prophet | 11.92 | 29.11% | 18.97% | 40.84% | 27.10% |
| V3_3_Prophet | 9.39 | 31.68% | 20.93% | 33.98% | 32.56% |
| V3_0_LR | 8.82 | 42.34% | 11.18% | 51.37% | 23.64% |
| V2_1_ARIMA | 8.38 | 31.62% | 24.19% | 70.80% | 18.99% |
| V2_3_ARIMA | 6.53 | 35.72% | 17.75% | 68.18% | 27.27% |
| V2_3_Prophet | 5.18 | 35.68% | 19.14% | 49.49% | 26.26% |
| V4_9_XGB | 4.29 | 49.20% | 15.71% | 69.82% | 19.70% |
| V4_15_XGB | 3.46 | 37.48% | 19.06% | 57.63% | 15.15% |
| V3_47_Prophet | 0.34 | 53.68% | 37.82% | 48.02% | 30.81% |
| V2_0_LR | 0.00 | 50.01% | 37.21% | 54.27% | 23.57% |
| V2_0_Prophet | 0.00 | 41.72% | 38.82% | 46.09% | 26.43% |
| V2_12_Prophet | 0.00 | 206.76% | 206.76% | 209.71% | 0.00% |
| V2_16_Prophet | 0.00 | 57.44% | 47.96% | 121.80% | 23.23% |
| V2_35_Prophet | 0.00 | 53.75% | 47.69% | 78.90% | 20.20% |
| V2_4_ARIMA | 0.00 | 43.67% | 28.10% | 63.89% | 20.78% |
| V3_3_XGB | 0.00 | 60.39% | 46.88% | 110.28% | 12.12% |
| V3_9_XGB | 0.00 | 58.75% | 43.51% | 81.48% | 12.63% |
| V4_0_LR | 0.00 | 219.57% | 180.17% | 273.58% | 4.04% |
| V4_1_XGB | 0.00 | 41.36% | 26.76% | 55.45% | 20.20% |

| Statistical Test | Result |
| --- | --- |
| Confidence Level | Low |
| P-Value (Wilcoxon) | 0.5298 |
| Weekly Win Rate | 51.52% |

| Data Quality Metric | Value |
| --- | --- |
| Coefficient of Variation | 7.59% |
| Identified Anomalies | 3 |
| Trend Direction | Flat |
