# Forecast Decision Intelligence Dashboard - Handover Document

## Overview
This project contains the **Enterprise Forecast Decision Intelligence Platform**, a specialized UI built to provide executive and analytical oversight into the performance of Machine Learning (ML) forecasts versus Manual forecasts. 

## File Structure: `/dashboard`

The `/dashboard` folder contains the production-ready code for the frontend UI. It is built using pure HTML, CSS, and Vanilla JavaScript, with Chart.js for data visualization. 

### Core Files
- **`index.html`**
  - **Functionality**: The master file containing all the HTML structure, inline CSS (for structural layout, KPI cards, and custom components), and the primary JavaScript logic (`initDashboard`) to render the data and charts.
  - **Key Sections**:
    - `<div class="sidebar">`: The left-hand navigation rail.
    - `id="page-exec"`: Executive Summary page containing the Decision Cockpit, dynamic Reveal Cards, and macro graphs.
    - `id="page-sa"`: Strategy Assessment page with ML vs. Manual WAPE comparisons, Tracking Signal bias charts, and Advantage Bands.
    - `id="page-mc"`: Model Champion page detailing the top algorithmic contenders.
    - `id="page-bc"`: Business Context page showing the historical baseline drop.
    - `id="page-ad"`: Anomaly Detection page highlighting structural breaks.

### Folders
- **`/data`**
  - **Functionality**: Stores the static JSON payloads that power the dashboard.
  - **`report.json`**: The primary data source fetched by `index.html` on load. Contains deeply nested analytical structures representing Strategy, Champions, Context, and Anomalies.

- **`/css` & `/js`** (If applicable/extended)
  - **Functionality**: Reserved for externalized stylesheets and scripts if the inline logic in `index.html` needs to be abstracted into separate bundles in the future.

## Key Design Principles Implemented
1. **Color Language**: 
   - **Teal (Green) (`#2F6F63`)**: Used consistently to represent Machine Learning / Algorithm performance.
   - **Navy (`#101B33`)**: Used for Manual Baselines and neutral/structural text.
   - **Rust (Red) (`#B3452B`)**: Used to represent the Manual forecast in comparative contexts, or negative anomalies.
2. **Interactive Elements**:
   - The **Reveal Cards** on the Executive Summary automatically expand to fit their content and flip on hover to reveal technical justifications.
   - The **Decision Cockpit** evaluates whether the ML's lead over the manual forecast meets the strict criteria needed for a fully unsupervised takeover. This decision is strictly democratic—it evaluates the winner (ML vs. Manual) on a queue-by-queue basis and aggregates the total win count, rather than being skewed by massive-volume queues.

## How to Run & Edit
- **To View**: Simply serve the directory using any local web server (e.g., `python -m http.server 8000`) and navigate to `http://localhost:8000/dashboard/`.
- **To Edit Data**: Modify the python backend scripts (located in the project root) that output to `dashboard/data/report.json`.
- **To Edit UI**: All structural and charting logic currently resides in `index.html`. Modifying the `Chart.js` instances inside the `initDashboard` function allows for rapid prototyping of new visualizations.
