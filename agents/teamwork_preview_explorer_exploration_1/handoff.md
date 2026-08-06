# Investigation Report: Data Slices, Filters, and Weekly Series Configuration

This report details how data slices, filters, and weekly series are structured in the frontend and backend of the Forecast Review Platform, along with a design proposal for adding filtered Q1 data (ML vs. Manual Strategy Assessment).

---

## 1. Observation

### Frontend (dashboard/js/app.js & dashboard/index.html)
- **Inline DATA Block**: `dashboard/js/app.js` contains a massive inline `DATA` object (specifically at line 2). A portion of the filters section under this block includes:
  ```json
  "filters": {
    "subregions": ["ANZ", "Brazil", "CCC", "CER", "EC", "IN", "JPN", "KR", "LATAM", "Multiple AMER SubRegions", "NER", "SA", "SER", "UKI"],
    "fiscal_years": ["2027", "2028"],
    "quarters": ["FQ1", "FQ2", "FQ3", "FQ4"],
    "slices": {
      "All|All|All": {
        "n_models": 92,
        "champion": "V2_9_Prophet",
        "champion_score": 75.32,
        "manual_wape": 17.84,
        "ml_wape": 21.11,
        "n_rows": 35640,
        "leaderboard": [...]
      },
      "All|All|FQ1": {...}
    }
  }
  ```
- **Filter Mapping & Retrieval**: 
  - `dashboard/js/app.js` binds filter elements at line 325-331:
    ```javascript
    const filterData = DATA.filters;
    const srSelect = document.getElementById('filter-subregion');
    const fySelect = document.getElementById('filter-fiscalyear');
    const qSelect = document.getElementById('filter-quarter');
    srSelect.innerHTML = '<option value="All">All Sub-Regions</option>' + filterData.subregions.map(s=>`<option value="${s}">${s}</option>`).join('');
    fySelect.innerHTML = '<option value="All">All Fiscal Years</option>' + filterData.fiscal_years.map(y=>`<option value="${y}">FY${y}</option>`).join('');
    qSelect.innerHTML = '<option value="All">All Quarters</option>' + filterData.quarters.map(q=>`<option value="${q}">${q}</option>`).join('');
    ```
  - Selection changes are handled dynamically via `renderQ2` at line 399-401:
    ```javascript
    function renderQ2(sr, fy, q){
      const key = `${sr}|${fy}|${q}`;
      const slice = filterData.slices[key];
      ...
    ```
- **Data Hydration/Overrides**: The frontend overrides `DATA` properties from `dashboard/data/report.json` on page load (lines 24-95). However, it only overrides core metadata and global-level metrics (e.g. `DATA.meta`, `DATA.executive`, `DATA.q1`, `DATA.q2.scatter`, etc.) and does **not** touch or override the `DATA.filters.slices` object.

### Asset Extraction (extract_js.py)
- The inline `DATA` block inside `app.js` is a static extraction from the monolithic HTML file `Forecast_Decision_Intelligence_Dashboard _1.html`.
- Line 4-9 of `extract_js.py` reads:
  ```python
  with open('Forecast_Decision_Intelligence_Dashboard _1.html', 'r', encoding='utf-8') as f:
      html = f.read()
  script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
  ```
  It splits the static HTML dashboard into separate HTML, CSS, and JS components, keeping the pre-calculated `DATA` block intact.

### Backend (generate_dashboard.py & services/forecast_review_service.py)
- **Patching JSON**: `generate_dashboard.py` reads the existing `report.json` and appends a `chart_data` block (lines 13-68):
  ```python
  chart_data = {"q1": {}, "q2": {}, "q3": {}, "q4": {}}
  # ... populates q1.series, q2.scatter, q2.boxplot, q3.series, q4.series
  data['chart_data'] = chart_data
  ```
- **Serialization**: `services/serialization.py` constructs the schema without generating or serializing any `slices` mapping for filters.

---

## 2. Logic Chain

1. **How `DATA.filters.slices` is populated**:
   - `DATA.filters.slices` is a static, pre-computed object embedded in `dashboard/js/app.js` (line 2). It was originally compiled in `Forecast_Decision_Intelligence_Dashboard _1.html` and extracted to `app.js` via `extract_js.py`.
   - On page load, `dashboard/js/app.js` fetches `dashboard/data/report.json`. It updates the global `DATA` metrics but leaves the `DATA.filters.slices` object intact. Consequently, the Q2 filtering system depends entirely on this hardcoded object.

2. **Where the slice generation code is located**:
   - There is **no** python code in the active repository that computes the multi-level combination slices (`SubRegion|FiscalYear|Quarter`).
   - The backend only computes single-level segment metrics (e.g., grouping by `Region` or `Channel` in `decision_orchestrator.py` via `get_segment_winners`) to recommend deployment models.

3. **How Q1 filtering (ML vs Manual) can be added**:
   - The Q1 strategy assessment page (`#page-q1`) currently has no filter bar and only renders global-level metrics (`DATA.q1.manual_wape`, `DATA.q1.ml_wape`, etc.) and `chart-q1` (global series).
   - Moving the filter bar to the global scope (Milestone M2) requires that filter changes affect Q1.
   - To achieve this, the Q1 metrics and weekly time series must be pre-calculated for each slice combination (`SubRegion|FiscalYear|Quarter`) and supplied to the frontend.

---

## 3. Caveats

- **Wilcoxon statistical significance**: Computing Wilcoxon p-values and effect sizes in the backend for every combinatoric slice could slow down report generation, as it involves running statistical tests over smaller sample sizes.
- **Insufficient row thresholds**: Filter combinations containing fewer than 30 rows for models are classified as "insufficient data". This logic is handled dynamically in `app.js` for Q2 but would need to be accounted for in Q1.

---

## 4. Conclusion & Proposed Implementation

To successfully add slices/filtered data for the Q1 Strategy Assessment page (ML vs. Manual) without performance degradation, we propose a **backend-driven pre-computation** approach.

### Step 1: Update the Backend to Generate Q1 Slices
We can extend `generate_dashboard.py` (or create a helper within the analytics package) to pre-calculate Q1 metrics for every combination of `SubRegion`, `Fiscal_Year`, and `Quarter`.

For each unique combination of `(SubRegion, Fiscal_Year, Quarter)`, we group the dataframe and compute:
1. **Manual WAPE**: `abs(Manual_Forecast - Actual_Offered).sum() / Actual_Offered.sum() * 100`
2. **ML WAPE**: `abs(ML_Forecast - Actual_Offered).sum() / Actual_Offered.sum() * 100`
3. **Weekly Series**: A timeline list of `{"week": date, "manual_wape": m_wape, "ml_wape": ml_wape}` for that slice.
4. **Wilcoxon p-value & Effect Size**: Pre-computed using `scipy.stats.wilcoxon` if sample size is sufficient (n >= 10).
5. **Win Rate**: The % of weeks where `Manual_Forecast` error was lower than `ML_Forecast` error.

The output will be saved in `report.json` under `chart_data.slices`:
```json
{
  "chart_data": {
    "slices": {
      "ANZ|2027|FQ1": {
        "q1": {
          "manual_wape": 15.2,
          "ml_wape": 16.5,
          "abs_improvement": -1.3,
          "manual_win_rate": 72.5,
          "p_value": 0.0032,
          "effect_size": 0.08,
          "confidence": "High",
          "series": [
            {"week": "2026-03-13", "manual_wape": 14.1, "ml_wape": 15.5}
          ]
        },
        "q2": {
          "leaderboard": [...],
          "champion": "V2_9_Prophet"
        }
      }
    }
  }
}
```

### Step 2: Move the Filter Bar and Wire the Frontend (app.js)
1. **HTML Layout Change**: Move the filter bar `div` in `index.html` from `#page-q2` to a global container above the pages.
2. **Render Binding**:
   - In `app.js`, when a filter changes, read the selected slice key (`${sr}|${fy}|${q}`).
   - Look up the slice in the parsed `reportData.chart_data.slices[key]`.
   - Update both Q2 (champion, leaderboard, composite scores) and Q1 UI components:
     ```javascript
     function renderQ1(slice) {
         if (!slice || !slice.q1) {
             // Show "insufficient data" or fallback to global Q1
             return;
         }
         // Update Q1 text metrics
         document.getElementById('q1-observation').textContent = `Manual WAPE was ${slice.q1.manual_wape}%. ML WAPE was ${slice.q1.ml_wape}%...`;
         // ... bind tables and text
         
         // Update Q1 chart
         const labels = slice.q1.series.map(d => d.week);
         lineChart('chart-q1', labels, [
             { label: 'Manual WAPE %', data: slice.q1.series.map(d => d.manual_wape), ... },
             { label: 'ML WAPE %', data: slice.q1.series.map(d => d.ml_wape), ... }
         ]);
     }
     ```

---

## 5. Verification Method

- **Functional Parity Checks**:
  Verify the changes by compiling the dashboard and ensuring that selecting filters (e.g. `ANZ`, `2027`, `All`) updates the curves on both the **Weekly WAPE (Q1)** line chart and the leaderboard/composite scores on **Q2**.
- **Execution of Tests**:
  Ensure all legacy tests continue to pass without regression:
  ```powershell
  pytest tests/verify_parity.py
  ```
