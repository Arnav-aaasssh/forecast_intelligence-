# Plan: Enterprise Forecast Decision Intelligence Dashboard Enhancements

## Architecture & Goals
- Make the existing filter bar (sub-region, fiscal year, fiscal quarter) global across the dashboard.
- Dynamically filter the "ML vs Manual" page (Q1) using client-side JavaScript.
- Brainstorm, design, and implement at least 2 new advanced analytical components on the dashboard to provide deeper, analyst-centric insights.
- Ensure the layout remains high-density, professional, and compliant with the Design Constitution (Observation before Recommendation, derived confidence, monospace numbers).

## Milestones

### Milestone 1: Exploration and Feasibility Analysis
- Explore `Forecast_Decision_Intelligence_Dashboard _1.html`, `dashboard/js/app.js`, and `dashboard/data/report.json` to understand how data slices, filtering, and chart objects are configured.
- Assess how the dataset is generated and parsed in `generate_dashboard.py` and `app.py`.
- Identify the exact mechanism to filter Q1 (ML vs Manual) data.

### Milestone 2: Global Filtering & Q1 Integration
- Move the HTML filter bar from `page-q2` to the global main wrapper (just below the header) in `dashboard/index.html`.
- Update `dashboard/js/app.js` to listen to filter events and dynamically re-calculate and re-render the Q1 "ML vs Manual" page contents, charts, and metrics based on the active filters.
- Re-run/update the chart data generation to support granular sliced data if needed.

### Milestone 3: Advanced Analytics Components
- Brainstorm and design two new analytical widgets for the dashboard:
  - **Component 1: Weekly Error Drift / Cumulative Bias Tracking Chart** (enables analysts to see if ML or Manual forecasts are systematically underestimating/overestimating demand over time).
  - **Component 2: Forecast Performance Heatmap Grid** (shows WAPE by Region and Channel to highlight which segments ML outperforms Manual, and where ML degrades).
- Implement the HTML/CSS/JS and backend data wiring for these components.

### Milestone 4: Visual Polish & Auditor Gate
- Audit color contrast, glassmorphism aesthetics, typography, and accessibility.
- Verify that confidence chips (High/Medium/Low) are styled and applied correctly.
- Ensure all numbers are mapped to real calculations and no recommendations are shown when confidence is Low.

### Milestone 5: E2E Verification & Review
- Run independent verification checks on the dashboard page.
- Obtain review approvals and compile final handoff.
