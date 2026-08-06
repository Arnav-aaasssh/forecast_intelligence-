# UX/UI Plan Report: Global Filter Bar Integration

## 1. Observation

### Verbatim File Paths & Line Numbers
- **`dashboard/index.html`**:
  - Lines 116-131: The filter bar is currently nested inside `#page-q2`:
    ```html
    <div class="filter-bar">
      <div class="filter-group">
        <label>Sub-Region</label>
        <select id="filter-subregion"></select>
      </div>
      <div class="filter-group">
        <label>Fiscal Year</label>
        <select id="filter-fiscalyear"></select>
      </div>
      <div class="filter-group">
        <label>Quarter</label>
        <select id="filter-quarter"></select>
      </div>
      <button class="reset-btn" id="filter-reset">Reset filters</button>
      <div class="filter-pills" id="filter-pills"></div>
    </div>
    ```
- **`dashboard/js/app.js`**:
  - Lines 325-331: Initializing select options:
    ```javascript
    const filterData = DATA.filters;
    const srSelect = document.getElementById('filter-subregion');
    const fySelect = document.getElementById('filter-fiscalyear');
    const qSelect = document.getElementById('filter-quarter');
    srSelect.innerHTML = '<option value="All">All Sub-Regions</option>' + filterData.subregions.map(s=>`<option value="${s}">${s}</option>`).join('');
    fySelect.innerHTML = '<option value="All">All Fiscal Years</option>' + filterData.fiscal_years.map(y=>`<option value="${y}">FY${y}</option>`).join('');
    qSelect.innerHTML = '<option value="All">All Quarters</option>' + filterData.quarters.map(q=>`<option value="${q}">${q}</option>`).join('');
    ```
  - Lines 459-464: Current event listeners call `renderQ2` only:
    ```javascript
    srSelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
    fySelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
    qSelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
    document.getElementById('filter-reset').addEventListener('click', ()=>{
      srSelect.value='All'; fySelect.value='All'; qSelect.value='All'; renderQ2('All','All','All');
    });
    ```
  - Lines 399-457: `renderQ2` extracts data from `filterData.slices[key]` (where `key = "${sr}|${fy}|${q}"`), updating leaderboard variables, KPIs, summary texts, and re-rendering `contribChart`.
  - Lines 186-201: The Q1 view text and KPI updates are hardcoded inside `renderDashboard()`, which executes once on `DOMContentLoaded` and does not support reactive updates.

- **`dashboard/data/report.json`**:
  - Line 76: Merged chart data block containing `q1` and `q3` time-series data.
  - Slices in `report.json` are pre-compiled and stored inside `DATA.filters.slices`. A typical slice contains aggregate values:
    ```json
    "n_models": 14,
    "champion": "V3_0_ARIMA",
    "champion_score": 55.09,
    "manual_wape": 20.2,
    "ml_wape": 23.85,
    "n_rows": 893,
    "leaderboard": [...]
    ```

---

## 2. Logic Chain

1. **Global Accessibility**: Placing `<div class="filter-bar">` inside `#page-q2` isolates the filters from other views. Relocating the filter bar to be a direct child of the `.wrap` container ensures it remains visible above any active page.
2. **Unified Filter Controller**: Replacing individual listeners that target `renderQ2` with a centralized handler `applyGlobalFilters()` allows coordinating updates to both Q1 and Q2 panels.
3. **Data Availability in Slices**: Slices contain aggregate `manual_wape`, `ml_wape`, and `n_rows` metrics.
   - For **Q1 Summary Metrics Table**: Slices supply the updated values for Manual WAPE, ML WAPE, and Row Counts (Sample Size). Absolute improvement can be computed dynamically as `slice.ml_wape - slice.manual_wape`.
   - For **Q1 Confidence and Recommendations**: Slices representing filtered data should display `Low` confidence with warnings stating that sub-sample significance testing is not pre-computed. Recommendations should be suppressed for filtered views, aligning with the conservative principles in `design_system.md`.
4. **Time-Series Chart Filtering**: `DATA.q1.series` contains weekly WAPE data points. When a user filters by Fiscal Year and Quarter, we can subset the series array in the frontend by checking the date strings (e.g. `'2027-05-14'`). When filtering by Sub-Region, since weekly sub-regional series are not present in `report.json`, the line chart should show a fallback state or message indicating that the timeline represents the global baseline, while the table displays the region's aggregate WAPE.

---

## 3. Caveats

- **Sub-Regional Time Series**: The JSON schema does not contain weekly series arrays per Sub-Region. As a result, when a Sub-Region is selected, the Q1 line chart cannot show regional-specific weekly trends and must fall back to showing the global weekly trend or a warning.
- **Statistical Sign-Rank Testing**: Sign-rank tests and p-values are only computed on the overall dataset (`All|All|All`). For filtered slices, the p-value and effect size are shown as "N/A" and confidence is downgraded to "Low".

---

## 4. Conclusion & Proposed Plan

### Step A: HTML Relocation
Move `<div class="filter-bar">` from `#page-q2` in `index.html` to be the first child of the `<div class="wrap">` container:
```html
<div class="wrap">
  <!-- Global Filter Bar -->
  <div class="filter-bar">
    <div class="filter-group">
      <label>Sub-Region</label>
      <select id="filter-subregion"></select>
    </div>
    <div class="filter-group">
      <label>Fiscal Year</label>
      <select id="filter-fiscalyear"></select>
    </div>
    <div class="filter-group">
      <label>Quarter</label>
      <select id="filter-quarter"></select>
    </div>
    <button class="reset-btn" id="filter-reset">Reset filters</button>
    <div class="filter-pills" id="filter-pills"></div>
  </div>

  <!-- Pages (Executive, Q1, Q2, etc.) -->
  <div class="page active" id="page-exec">...</div>
  <div class="page" id="page-q1">...</div>
  <div class="page" id="page-q2">...</div>
  ...
</div>
```

### Step B: JS Controller Refactoring (`app.js`)
Introduce a centralized controller `applyGlobalFilters` and bind it to the select element change events:
```javascript
// Central Controller
function applyGlobalFilters() {
  const sr = srSelect.value;
  const fy = fySelect.value;
  const q = qSelect.value;

  renderQ1(sr, fy, q);
  renderQ2(sr, fy, q);
}

// Bind Listeners
srSelect.addEventListener('change', applyGlobalFilters);
fySelect.addEventListener('change', applyGlobalFilters);
qSelect.addEventListener('change', applyGlobalFilters);
document.getElementById('filter-reset').addEventListener('click', () => {
  srSelect.value = 'All';
  fySelect.value = 'All';
  qSelect.value = 'All';
  applyGlobalFilters();
});
```

### Step C: JS Q1 Reactive Rendering (`app.js`)
Define `renderQ1(sr, fy, q)` to dynamically refresh the Strategy Assessment page:
```javascript
let q1ChartInstance = null; // Store chart globally to allow dynamic updates

function renderQ1(sr, fy, q) {
  const key = `${sr}|${fy}|${q}`;
  const slice = filterData.slices[key];

  if (!slice) {
    // Insufficient Data State
    document.getElementById('q1-observation').textContent = 'Insufficient data for Q1 evaluation in this slice.';
    document.getElementById('q1-conclusion').textContent = 'Cannot compare performance.';
    document.getElementById('q1-decision-support').textContent = 'Broaden filters to increase sample size.';
    document.getElementById('q1-rec').textContent = 'Recommendation suppressed: insufficient data.';
    document.getElementById('q1-primary').innerHTML = '<tr><td colspan="2">No data</td></tr>';
    document.getElementById('q1-supporting').innerHTML = '<tr><td colspan="2">No data</td></tr>';
    return;
  }

  // Calculate Metrics
  const manualWAPE = slice.manual_wape;
  const mlWAPE = slice.ml_wape;
  const diff = mlWAPE - manualWAPE;
  const absImp = Math.abs(diff).toFixed(2) + 'pp';
  const labelImp = diff < 0 ? 'Absolute Improvement (ML vs Manual)' : 'Absolute Increase in ML Error';
  
  // Is it the overall dataset?
  const isGlobal = (sr === 'All' && fy === 'All' && q === 'All');
  
  // Update Q1 text
  document.getElementById('q1-observation').textContent = 
    `Manual WAPE was ${manualWAPE.toFixed(2)}%. ML WAPE was ${mlWAPE.toFixed(2)}%. Evaluated across ${slice.n_rows.toLocaleString()} records.`;
  
  document.getElementById('q1-conclusion').textContent = isGlobal
    ? 'Manual forecasts were more accurate than the aggregate ML system, with high statistical confidence.'
    : 'Comparative WAPE figures for this segment. Statistical testing not pre-computed for sub-samples.';

  document.getElementById('q1-decision-support').textContent = isGlobal
    ? 'Persistently higher aggregate ML error was associated with more forecasting misses across the evaluation window.'
    : 'Sub-regional or sub-temporal performance may vary. Global baseline significance must be considered.';

  // Suppress recommendations on filtered slices
  document.getElementById('q1-rec').innerHTML = isGlobal
    ? chip('High') + ' &nbsp;Retain the Manual Forecast as the primary production forecasting method.'
    : 'Recommendation suppressed: significance testing is only conducted on the global population.';

  // Update Tables
  document.getElementById('q1-primary').innerHTML = `
    <tr><td>Manual WAPE</td><td>${manualWAPE.toFixed(2)}%</td></tr>
    <tr><td>ML WAPE</td><td>${mlWAPE.toFixed(2)}%</td></tr>
    <tr><td>${labelImp}</td><td>${absImp}</td></tr>`;

  document.getElementById('q1-supporting').innerHTML = `
    <tr><td>Weekly Win Rate (Manual)</td><td>${isGlobal ? DATA.q1.manual_win_rate + '%' : 'N/A (filtered)'}</td></tr>
    <tr><td>Statistical Significance (p)</td><td>${isGlobal ? DATA.q1.p_value.toExponential(3) : 'N/A'}</td></tr>
    <tr><td>Effect Size</td><td>${isGlobal ? DATA.q1.effect_size : 'N/A'}</td></tr>
    <tr><td>Sample Size (Rows)</td><td>${slice.n_rows.toLocaleString()}</td></tr>`;

  // Update Q1 Line Chart
  let filteredSeries = DATA.q1.series;
  if (fy !== 'All') {
    filteredSeries = filteredSeries.filter(d => getFiscalYear(d.week) === fy);
  }
  if (q !== 'All') {
    filteredSeries = filteredSeries.filter(d => getFiscalQuarter(d.week) === q);
  }

  // Render or Update chart
  const labels = filteredSeries.map(d => d.week);
  const manualData = filteredSeries.map(d => d.manual_wape);
  const mlData = filteredSeries.map(d => d.ml_wape);

  if (q1ChartInstance) {
    q1ChartInstance.data.labels = labels;
    q1ChartInstance.data.datasets[0].data = manualData;
    q1ChartInstance.data.datasets[1].data = mlData;
    q1ChartInstance.update();
  } else {
    q1ChartInstance = lineChart('chart-q1', labels, [
      {label:'Manual WAPE %', data: manualData, borderColor:COLORS.navy, backgroundColor:COLORS.navy+'15', borderWidth:2, pointRadius:0, tension:.25},
      {label:'ML WAPE %', data: mlData, borderColor:COLORS.rust, backgroundColor:COLORS.rust+'15', borderWidth:2, pointRadius:0, tension:.25}
    ]);
  }
}

// Utility Helper functions
function getFiscalYear(dateStr) {
  // Extract year from YYYY-MM-DD
  return dateStr.split('-')[0];
}

// Map calendar months to Fiscal Quarters
function getFiscalQuarter(dateStr) {
  const month = parseInt(dateStr.split('-')[1]);
  if (month >= 4 && month <= 6) return 'FQ1';
  if (month >= 7 && month <= 9) return 'FQ2';
  if (month >= 10 && month <= 12) return 'FQ3';
  return 'FQ4'; // Jan-Mar
}
```

---

## 5. Verification Method

To verify the correct behavior of the relocated global filter bar and reactive rendering:
1. **Layout Placement**: Open `dashboard/index.html` in a web browser. Confirm the filter bar remains visible at the top of the content panel when switching between page tabs in the left navigation rail.
2. **State Updates (Q1 & Q2)**: Select a filter (e.g. `Fiscal Year: FY2027` or `Quarter: FQ3`). Verify that:
   - On the **Strategy Assessment (Q1)** page, the weekly WAPE line chart updates to show only the matching weeks, and the summary table values update.
   - On the **Model Champion (Q2)** page, the champion model, composite score, runner-up, and family contribution charts update.
3. **Reset Behavior**: Click the **Reset filters** button and verify all dropdowns revert to `All` and both Q1 and Q2 return to their baseline states.
