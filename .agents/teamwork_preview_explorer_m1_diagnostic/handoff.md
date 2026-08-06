# Diagnostic Investigation Report: Dashboard Q2 Rendering & Global Filter Failures

This report details the root causes of the Q2 page rendering failure and the global dropdown filter malfunction in the Forecast Decision Intelligence Dashboard, alongside the exact logic and code changes required to restore full functionality.

---

## 1. Observation

Direct observations from the codebase files:

### A. Undefined Variable `qSelect` throwing ReferenceError
In `dashboard/js/app.js`, lines 649–654:
```javascript
649: srSelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
650: fySelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
651: qSelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
652: document.getElementById('filter-reset').addEventListener('click', ()=>{
653:   srSelect.value='All'; fySelect.value='All'; qSelect.value='All'; renderQ2('All','All','All');
654: });
```
* **Observation**: `qSelect` is referenced on lines 649, 650, 651, and 653, but is never declared or defined in the codebase.
* **Observation**: In `dashboard/index.html` (lines 43–60), the global filter bar has only three select elements: `#filter-subregion`, `#filter-fiscalyear`, and `#filter-channel`. There is no element for quarters.

### B. Mismatched Slice Key Lookups for Q2
In `dashboard/js/app.js`, line 591:
```javascript
591:   const slice = filterData.slices[key];
```
* **Observation**: `filterData` is referenced but is not declared. The correct data object is `DATA.filters.slices`, which contains keys corresponding to `Subregion|FiscalYear|Quarter` (e.g. `'ANZ|2027|All'`).
* **Observation**: The default values of the dropdown selectors in `dashboard/index.html` (lines 47, 51, 55) are `"all"` (lowercase). However, in `app.js` (lines 583–585) and the keys of `DATA.filters.slices`, `"All"` is capitalized (e.g., `'All|All|All'`). This casing mismatch causes slice lookup failures when filters are in their default state.

### C. Overriding Duplicate Functions (`updateFilterPills`)
In `dashboard/js/app.js`:
* Lines 494–502:
  ```javascript
  function updateFilterPills() {
    const pills = document.getElementById('filter-pills');
    if (!pills) return;
    const parts = [];
    const sr = srSelect?.value; if (sr && sr !== 'all') parts.push(`Sub-Region: ${sr}`);
    const fy = fySelect?.value; if (fy && fy !== 'all') parts.push(`FY${fy}`);
    const ch = chSelect?.value; if (ch && ch !== 'all') parts.push(`Channel: ${ch}`);
    pills.innerHTML = parts.map(p => `<span class="pill">${p}</span>`).join('');
  }
  ```
* Lines 580–587:
  ```javascript
  function updateFilterPills(sr, fy, q){
    const pills = document.getElementById('filter-pills');
    let html = '';
    html += sr==='All' ? '<span class="pill neutral">Sub-Region: All</span>' : `<span class="pill">Sub-Region: ${sr}</span>`;
    html += fy==='All' ? '<span class="pill neutral">Fiscal Year: All</span>' : `<span class="pill">Fiscal Year: FY${fy}</span>`;
    html += q==='All' ? '<span class="pill neutral">Quarter: All</span>' : `<span class="pill">Quarter: ${q}</span>`;
    pills.innerHTML = html;
  }
  ```
* **Observation**: The second definition overrides the first due to JavaScript function hoisting and redeclaration. Since `onFilterChange` calls `updateFilterPills()` with no arguments, the parameters `sr`, `fy`, and `q` evaluate to `undefined`, breaking the filter pill displays.

### D. Mutually Exclusive Filter Overrides in Q1 Series Filtering
In `dashboard/js/app.js`, lines 282–295:
```javascript
  // Sub-region filter
  if (sr !== 'all' && DATA.q1.slices_subregion && DATA.q1.slices_subregion[sr]) {
    series = DATA.q1.slices_subregion[sr];
  }
  // Fiscal year filter
  if (fy !== 'all' && DATA.q1.slices_fiscalyear && DATA.q1.slices_fiscalyear[fy]) {
    series = series.filter(d => d.week.startsWith(fy === '2027' ? '2026' : fy));
    // Use fiscal-year slice if available
    const fySlice = DATA.q1.slices_fiscalyear[fy];
    if (fySlice) series = fySlice;
  }
  // Channel filter
  if (ch !== 'all' && DATA.q1.slices_channel && DATA.q1.slices_channel[ch]) {
    series = DATA.q1.slices_channel[ch];
  }
```
* **Observation**: Selecting multiple filters causes subsequent steps to overwrite `series` completely (e.g., selecting a Channel overwrites the sub-region filtered series: `series = DATA.q1.slices_channel[ch]`).
* **Observation**: `biasSeries` is declared on line 279 as `let biasSeries = DATA.q1.bias_drift || [];` but is never modified or filtered. As a result, the Bias Drift chart remains static.

### E. Static Page Metric Elements
* **Observation**: Static text summaries and KPI card headlines (e.g. `#exec-summary-text`, `#navcard-q1-headline`, `#navcard-q2-headline`, `#exec-observation`, `#q1-observation`, `#q1-primary`, `#q1-supporting`) are only updated once on page load inside `renderDashboard()` (lines 141–183). Changing dropdown filters does not update these text values.

---

## 2. Logic Chain

1. **ReferenceError Halt**: The engine attempts to run `renderDashboard()` on load. When execution reaches line 649, referencing the undeclared `qSelect` throws a `ReferenceError`.
2. **Missing KPIs and Leaderboard**: Because execution halts at line 649, subsequent code on lines 656 (`renderQ2('All', 'All', 'All')`) and lines 659–708 (Q2 Chart definitions) is never reached. This leaves Q2 KPI text fields empty and the leaderboard, scatter plot, and boxplot unrendered.
3. **Broken Global Filters**:
   - The dropdown listeners for Q2 fail on load because of the ReferenceError.
   - The duplicate `updateFilterPills` function overrides the channel-aware pill logic, creating `undefined` pills.
   - Overwriting `series` for each active dropdown selector prevents combinations (e.g. Sub-Region AND Fiscal Year) from working.
   - Omitting `biasSeries` from the filtering logic keeps the Bias Drift chart permanently static.
   - Restricting text updates to the initial page load leaves the visual text disconnected from chart filter changes.

---

## 3. Caveats

* **Quarter Selector**: There is no Quarter select dropdown in `index.html`. We assume Quarter should default to `"All"` during Q2 leaderboards lookups unless a select element is explicitly added.
* **Pre-computed Multi-dimensional Slices**: The Q1 backend-computed slices are single-dimension only (`slices_subregion`, `slices_channel`, `slices_fiscalyear`). Multi-dimensional filtering (e.g. ANZ + Voice) is achieved by subsetting the single-dimension slice by year (since weeks are dated). Filtering by both Region AND Channel is not supported by the pre-computed slices and defaults to Region priority.
* **Bias Drift Segment slices**: The backend dataset (`report.json`) does not contain sliced tracking signal data for Sub-Regions or Channels. Therefore, the Bias Drift chart can only be filtered by Fiscal Year.

---

## 4. Conclusion

The rendering and filter failures are software bugs in `dashboard/js/app.js` caused by:
1. Referencing undefined variables (`qSelect`, `filterData`).
2. Duplicated function declarations.
3. Overwriting series arrays rather than subsetting them sequentially.
4. Omitting filter logic for `biasSeries` and static text DOM elements.

### Proposed Implementation Plan:

#### Step 1: Clean up `app.js` global event registrations
* Remove the broken event listeners on lines 649–654.
* Bind all three global filters to call a single, unified `onFilterChange()` function.

#### Step 2: Refactor `getFilteredQ1Series`
* Implement cumulative filtering where selecting a year subsets the weeks of the active Sub-Region/Channel slice.
* Filter `biasSeries` by matching week dates inside the selected Fiscal Year slice.

#### Step 3: Implement dynamic text and KPI card updates
* Write an `updateTextMetrics()` helper called inside `onFilterChange()` to calculate overall WAPE, win rates, and update HTML texts and KPI blocks.

#### Step 4: Fix Q2 slice lookups and render integrations
* Correct `filterData.slices` to `DATA.filters.slices`.
* Standardize `"all"` (from selector value) to `"All"` (for slice key lookup).
* Call `renderQ2` dynamically during `onFilterChange`.

---

## 5. Verification Method

To verify these changes:
1. **Load Dashboard**: Ensure there are no JavaScript errors in the browser console. Inspect the Q2 page to check that KPI cards (Champion model, composite score, runner-up) and the four Q2 charts render correctly.
2. **Apply Filters**: Select a Sub-Region (e.g., `'ANZ'`) or Fiscal Year (e.g., `'2027'`). Verify:
   - The Q1 WAPE chart, Bias Drift chart, and histogram update immediately.
   - The KPI cards and summary texts on both the Executive and Q1 views reflect the filtered values.
   - The Q2 Champion, Composite Score, and Leaderboard table update to the matching slice.
3. **Reset Filters**: Click "Reset Filters". Ensure all views return to their global unfiltered state and all stats match the values in `report.json`.
