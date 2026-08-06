## 2026-07-13T14:58:34Z
Objective: Implement the global filter bar integration, reactive Q1/Q2 rendering, and advanced analytics components.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Detailed Instructions:
1. Check the columns of the raw Excel dataset (sample_data/FinalForecast_Imputed.xlsx) via python to see what columns represent Region/Sub-Region, Fiscal Year, and Fiscal Quarter.
2. Relocate the filter-bar div in `dashboard/index.html` from `#page-q2` to be the first child of the `<div class="wrap">` container, making it globally visible.
3. Modify `generate_dashboard.py` to:
   - Calculate pre-computed Q1 metrics (manual_wape, ml_wape, n_rows, win_rate, p_value, effect_size) and the weekly time series (`series` list of `{"week": date, "manual_wape": m_wape, "ml_wape": ml_wape}`) for every filter combination of Sub-Region, Fiscal Year, and Quarter. Write these into a `slices` block in `report.json` under `chart_data.slices`.
   - Calculate weekly Tracking Signal (TS) series for the ML Champion and Manual Baseline:
     - e_t = Actual_t - Forecast_t
     - AE_t = abs(e_t)
     - CFE_t = sum(e_i) from i=1 to t
     - MAD_t = (sum(AE_i) from i=1 to t) / t
     - TS_t = CFE_t / MAD_t (if MAD_t == 0, TS_t = 0)
     Write these series into `chart_data.q1.cumulative_drift` inside `report.json`.
   - Calculate Region x Channel performance metrics for the WAPE Heatmap grid. For each of the 3 Regions (APJ, Americas, EMEA) and 5 Channels (Voice, Chat, Email, Case, Social Media), compute the aggregate ML WAPE and Manual WAPE. Write these to `chart_data.q2.segment_grid` inside `report.json`.
4. Modify `dashboard/js/app.js` to:
   - Read the pre-calculated slices from `reportData.chart_data.slices` on load and populate `DATA.filters.slices` in-memory.
   - Centralize filter change listeners to call both `renderQ1(sr, fy, q)` and `renderQ2(sr, fy, q)`.
   - Implement `renderQ1` to dynamically update the Q1 WAPE line chart (subsetting the weekly series), update the primary/supporting metrics tables, and update the observation/conclusion text. If a filtered slice is selected, set confidence to 'Low' and suppress recommendations.
   - Implement the Tracking Signal Line Chart (Component 1) in the Q1 page using Chart.js on a new `<canvas id="chart-q1-drift"></canvas>` element inside `dashboard/index.html`. Add control limit reference lines at y = +4.0 and -4.0 (amber), normal neutral line at y = 0, and style the datasets (ML: teal, Manual: gray).
   - Implement the WAPE Performance Heatmap Grid (Component 2) in the Q2 page using a new HTML table container `<div id="q2-heatmap-grid"></div>` inside `dashboard/index.html`. Color code each cell dynamically based on Delta = Manual WAPE - ML WAPE: Teal soft background (#E4EFEC) and Teal text (#2F6F63) if Delta > +2.0%, Rust soft background (#FBE9E4) and Rust text (#B3452B) if Delta < -2.0%, otherwise Gray soft background (#EDEFF2) and Dark text.
5. In `dashboard/css/styles.css`, add any required CSS styles for the new heatmap grid and tracking signal layout, ensuring WCAG AA compliance (use #4A5361 dark gray text for low confidence chips and gray text on light gray backgrounds).
6. Verify your implementation by running the application pipeline on the sample dataset:
   `python app.py sample_data/FinalForecast_Imputed.xlsx`
   Then run existing tests:
   `pytest tests/`

Working directory: d:\project_1 imp docs\Forecast review\agents\teamwork_preview_worker_implementation\
Write your changes report and verification outcomes to handoff.md in your working directory.
