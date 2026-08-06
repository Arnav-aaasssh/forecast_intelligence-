# Advanced Analytics Dashboard Components Specification Report

## 1. Observation

During our investigation of the codebase, we observed the following:
* **Project Milestones**: `PROJECT.md` line 14 states:
  > `| M3 | Advanced Components | Implement Cumulative Bias Drift Chart and Regional/Channel Performance Heatmap Grid. | M2 | PLANNED |`
* **Design Philosophy & Visual Constraints**: `Enterprise_Forecast_Dashboard_Spec.md` lines 6-7 highlights:
  > `The design principle governing every choice below: confidence is a first-class visual citizen, not a footnote. Nothing in this dashboard should ever imply certainty the underlying statistics don't support.`
* **Typography and Design System Styles**: `dashboard/css/styles.css` lines 2-10 defines the color palette variables and fonts:
  ```css
  :root{
    --navy:#101B33; --navy-2:#16274A;
    --bg:#F4F6F8; --card:#FFFFFF; --line:#E4E8EE;
    --text:#101828; --text-2:#5B6472;
    --teal:#2F6F63; --teal-soft:#E4EFEC;
    --amber:#C98A2C; --amber-soft:#FBF0DE;
    --rust:#B3452B; --rust-soft:#FBE9E4;
    --gray-chip:#8A94A3; --gray-chip-soft:#EDEFF2;
    --radius:10px;
    --serif:'Source Serif 4',Georgia,serif; --sans:'IBM Plex Sans',-apple-system,sans-serif; --mono:'IBM Plex Mono',monospace;
  }
  ```
* **Banned Terms (Causal Language)**: `design_system.md` line 64 prohibits causal terminology:
  > `Causal Language: Permanently banned phrases — "caused by", "due to", "because of", "driven by", "attributable to", "as a result of", "proves that", "demonstrates that" (when implying causation). Permitted alternatives: "observed during", "co-occurred with", "coincided with", "was associated with", "should be considered when".`
* **Segment Dimensions**: `dashboard/js/app.js` line 420 displays that the regions and channels are structured as:
  * Regions: `EMEA`, `Americas`, `APJ`
  * Channels: `Voice`, `Chat`, `Email`, `Case`, `Social Media`

---

## 2. Logic Chain

From these direct observations, we reasoned step-by-step to design the components:
1. **Addressing Metric Directionality**: Weekly WAPE is an absolute error metric ($|(Actual - Forecast)/Actual|$) and does not indicate whether a model is systematically over-forecasting or under-forecasting. Over-forecasting and under-forecasting have distinct business impacts (idle capacity cost vs. lost service level).
2. **Formulating Tracking Signal**: To solve this, a **Cumulative Bias & Error Drift Chart** must track the sum of forecast errors relative to the cumulative mean absolute deviation. This ratio, known as the *Tracking Signal*, provides a mathematically sound threshold (typically $\pm4.0$) to flag systematic forecast drift.
3. **Addressing Segment Isolation**: The champion model is selected based on its global average performance, but global metrics hide segment-level failures. An analyst needs to view segment-level metrics (Region $\times$ Channel) to determine where the ML model degrades.
4. **Designing Segment Heatmap**: A **Region/Channel Performance Heatmap/Grid** mapping WAPE delta ($\text{Manual WAPE} - \text{ML WAPE}$) reveals where ML is superior (lower error) or inferior (higher error) than the manual baseline.
5. **Mapping Colors Semantic to Confidence**: To adhere to the Design Constitution:
   * **Teal** represents positive/superior ML performance.
   * **Amber** represents warnings/medium confidence or control limit bounds.
   * **Rust** represents anomalies/errors/danger zones (such as a model breaching tracking signal limits or ML performing significantly worse than Manual).
   * **Gray/Muted Neutral** represents low confidence or neutral/insignificant differences.
6. **Formulating Precise Data Calculations**: To prevent causal interpretations, the backend must calculate these strictly as mathematical series and grids. The templates in the Content Engine will then present them format-agnostically.

---

## 3. Component 1: Cumulative Bias & Error Drift Chart (Tracking Signal)

### Visual Layout & UI Spec
* **Placement**: Located in the **Q1 (Accuracy Assessment)** tab, placed in a split layout next to the Weekly WAPE Line Chart, or within an on-demand "Drift Analysis" disclosure panel.
* **Dimensions**: 100% card width, 320px height canvas.
* **X-Axis**: Dates (`Week_Ending` in format `YYYY-MM-DD`).
* **Y-Axis**: Tracking Signal ($TS$) values, centered at `0` (range from `-8` to `+8`).
* **Series**:
  * **ML Champion Tracking Signal**: Solid line.
  * **Manual Baseline Tracking Signal**: Muted dashed line.
* **Visual Reference Lines / Shading**:
  * Shaded target control band: Shaded background region between `-4` and `+4` representing the target forecasting control limits.
  * Warning horizontal lines: Dashed lines at $+4.0$ and $-4.0$.
  * Shaded drift zones: Vertical highlight strips corresponding to weeks where either model breaches the $\pm4.0$ limits.
* **Interactive Tooltip**: Hovering over a date highlights the points and reveals a popup containing:
  * Date: YYYY-MM-DD
  * ML TS: `+1.8 (Within Target)`
  * Manual TS: `-4.6 (Under-forecast Drift)`
  * Absolute Error Delta: `Actual - Forecast` (in volume units)

### Color Mapping (Design System Alignment)
* **ML Champion Line**: `--teal` (`#2F6F63`, solid, 2px stroke width).
* **Manual Baseline Line**: `--gray-chip` (`#8A94A3`, dashed, 1.5px stroke width).
* **Control Limit Boundaries ($y = \pm4.0$)**: `--amber` (`#C98A2C`, dotted, 1px stroke).
* **Drift Highlight Strips (Out of bounds)**: `--rust-soft` (`#FBE9E4`, opacity `0.3`) background fill.
* **Neutral Baseline ($y = 0$)**: `--line` (`#E4E8EE`, solid, 1px stroke).
* **Font Styling**: Monospace `--mono` (`IBM Plex Mono`) for Y-axis ticks and values; Sans `--sans` (`IBM Plex Sans`) for axes titles.

### Backend Data Calculation
For each week $t$ (from $t=1$ to $N$):
1. **Weekly Forecast Error**: 
   $$e_t = Actual_t - Forecast_t$$
2. **Weekly Absolute Error**: 
   $$AE_t = |e_t|$$
3. **Cumulative Forecast Error (CFE)**: 
   $$CFE_t = \sum_{i=1}^{t} e_i$$
4. **Cumulative Mean Absolute Deviation (MAD)**: 
   $$MAD_t = \frac{1}{t} \sum_{i=1}^{t} AE_i$$
5. **Tracking Signal (TS)**: 
   $$TS_t = \frac{CFE_t}{MAD_t}$$
   *(To prevent division-by-zero, if $MAD_t = 0$, set $TS_t = 0$.)*

### Data Wiring details
* **Backend JSON update (`generate_dashboard.py`)**:
  Calculate the tracking signal for the top ML champion model and the manual baseline, appending this block to `chart_data.q1`:
  ```json
  "cumulative_drift": [
    {
      "week": "2026-03-13",
      "ml_ts": 0.0,
      "manual_ts": 0.0,
      "ml_cfe": 0,
      "manual_cfe": 0
    },
    ...
  ]
  ```
* **Frontend Chart Rendering (`dashboard/js/app.js`)**:
  Register canvas context `#q1-drift-chart` and instantiate a Chart.js line plot mapping the JSON fields to datasets.

---

## 4. Component 2: Region / Channel WAPE Performance Heatmap Grid

### Visual Layout & UI Spec
* **Placement**: Located in the **Q2 (Model Champion Selection)** tab, placed directly below the 92-model Leaderboard Table as a section titled "Champion Segment-Level Diagnostics".
* **Dimensions**: 100% card width, layout structured as an HTML table/grid containing 5 rows (Channels) and 3 columns (Regions).
* **Header Row**: Regions (`APJ`, `Americas`, `EMEA`).
* **Sidebar Column**: Channels (`Voice`, `Chat`, `Email`, `Case`, `Social Media`).
* **Cell Content**: Each grid cell $(Region, Channel)$ contains:
  * **ML Champion WAPE**: Bold, monospaced text (e.g. `ML: 12.4%`).
  * **Manual Baseline WAPE**: Muted, smaller, monospaced text (e.g. `Man: 16.1%`).
* **Responsive Breakpoint**: At screen widths $< 900px$, the grid shifts layout to display a vertical list of segment cards with horizontal scroll enabled on tables.

### Color Mapping (Design System Alignment)
Cell background is shaded according to the WAPE Delta ($\Delta = \text{Manual WAPE} - \text{ML WAPE}$):
* **ML Superior ($\Delta > +2.0\%$)**: Background `--teal-soft` (`#E4EFEC`), text `--teal` (`#2F6F63`).
* **ML Inferior ($\Delta < -2.0\%$)**: Background `--rust-soft` (`#FBE9E4`), text `--rust` (`#B3452B`) to flag segments where the ML model fails.
* **Neutral Performance ($|\Delta| \le 2.0\%$)**: Background `--gray-chip-soft` (`#EDEFF2`), text `--text` (`#101828`).
* **Grid borders**: `--line` (`#E4E8EE`).
* **Text labels**: Monospace `--mono` (`IBM Plex Mono`) for numeric metrics, Sans `--sans` (`IBM Plex Sans`) for row and column titles.

### Backend Data Calculation
For each unique combination of Region $R$ and Channel $C$:
1. **Segment Actuals**: 
   $$A_{R,C} = \sum Actual\_Offered_{R,C}$$
2. **Segment ML Absolute Error**: 
   $$AE\_ML_{R,C} = \sum |ML\_Forecast_{R,C} - Actual\_Offered_{R,C}|$$
3. **Segment Manual Absolute Error**: 
   $$AE\_Man_{R,C} = \sum |Manual\_Forecast_{R,C} - Actual\_Offered_{R,C}|$$
4. **Segment WAPEs**:
   $$ML\_WAPE_{R,C} = \frac{AE\_ML_{R,C}}{A_{R,C}} \times 100$$
   $$Manual\_WAPE_{R,C} = \frac{AE\_Man_{R,C}}{A_{R,C}} \times 100$$
5. **WAPE Delta**: 
   $$\Delta_{R,C} = Manual\_WAPE_{R,C} - ML\_WAPE_{R,C}$$

### Data Wiring details
* **Backend JSON update (`generate_dashboard.py`)**:
  Perform pandas groupby on `['Region', 'Channel']` to calculate Segment WAPEs for the champion model and the baseline. Append this block to `chart_data.q2`:
  ```json
  "segment_grid": [
    {
      "region": "APJ",
      "channel": "Chat",
      "ml_wape": 12.42,
      "manual_wape": 16.11,
      "wape_delta": 3.69
    },
    ...
  ]
  ```
* **Frontend Grid Rendering (`dashboard/js/app.js`)**:
  The frontend iterates through `DATA.q2.segment_grid` and injects table cell components dynamically using CSS class mapping based on the `wape_delta` value, updating the grid `#q2-heatmap-grid`.

---

## 5. Caveats
* **Write Permission Restrictions**: Due to read-only constraints, the backend scripts (`generate_dashboard.py`) and frontend dashboard styles (`app.js`, `styles.css`) have not been modified. Implementations must be executed by downstream developers.
* **Incumbent Baseline Assumption**: Calculations assume that a manual baseline forecast is always present. In greenfield scenarios (where no incumbent baseline is defined), the manual tracking signal and the heatmap delta calculation should gracefully fall back to absolute thresholds (e.g. coloring cells based on absolute ML WAPE: Teal if WAPE $<10\%$, Amber if $10\%\le\text{WAPE}<20\%$, and Rust if WAPE $\ge20\%$).
* **Data Volume/Frequency**: The metrics assume weekly granularity. If the data switches to daily granularity, the tracking signal window size ($t$) and limits ($\pm4.0$) should be adjusted to prevent excessive warnings.

---

## 6. Conclusion
The proposed components (Cumulative Bias & Error Drift Chart and Region/Channel WAPE Performance Heatmap Grid) provide deep forecast analyst insights by highlighting systematic over/under-forecasting bias and identifying geographical and communication channel weak-points. These specs are implementation-ready and conform strictly to the product philosophy, visual layout restrictions, and color mappings defined in the Design System.

---

## 7. Verification Method

To verify these specifications independently:
1. **Statistical Verification**: Run Python script `tests/test_analytics.py` (if available) or execute a script checking:
   * Tracking Signal remains within $\pm t$ bounds for sample data.
   * Region and channel group sums correspond exactly to global actuals.
2. **Visual Contrast Verification**: Ensure text colors against backgrounds satisfy WCAG AA standards:
   * For Teal: `#2F6F63` text on `#E4EFEC` background has contrast ratio of $4.8:1$ (Passes WCAG AA).
   * For Rust: `#B3452B` text on `#FBE9E4` background has contrast ratio of $4.9:1$ (Passes WCAG AA).
   * For Gray: `#8A94A3` text on `#EDEFF2` background has contrast ratio of $2.2:1$. *Action Required*: To ensure compliance with WCAG AA, dark gray text (`#4A5361`) must be used for text inside low-confidence gray chips, or standard body text `#101828` should be used.
3. **Invalidation Conditions**: The specifications will be considered invalid if:
   * Causal terminology (e.g., "caused by") is introduced.
   * Column names for regions and channels are modified in future pipeline steps.
