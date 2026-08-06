# Original User Request

## 2026-07-13T09:07:26Z

# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval.
> Goal: Get user approval → delegate to teamwork_preview

An autonomous 5-agent organization (Coding, Review, Design, Product Improvement, Coordination) collaboratively developing the **Enterprise Forecast Decision Intelligence Platform** following strict enterprise software delivery protocols.

Working directory: `D:\project_1 imp docs\Forecast review`
Integrity mode: `development`

## Requirements

### R1. Multi-Agent Software Delivery Organization
The team must operate as a 5-agent organization:
1. **Coordination Agent**: Project orchestration, task assignment, and conflict resolution.
2. **Product Improvement Agent**: Suggests workflow and product enhancements.
3. **Design Agent**: Presentation layer excellence (UI/UX, accessibility, aesthetics).
4. **Coding Agent**: Implements approved work (source code, clean code, correctness).
5. **Review Agent**: Independent QA, architecture compliance, and bug identification.
*Rule: No implementation can be completed without passing through the full multi-agent review process.*

### R2. Software Requirements
The team must implement the following features on the "ML vs Manual" page:
1. **Global Filtering:** Apply the existing filters (sub-region, fiscal year, fiscal quarter) so that they dynamically filter the data shown on the ML vs Manual page.
2. **Advanced Analytics Components:** Brainstorm, design, and implement additional advanced dashboard components (charts, metrics, grids) that would impress a forecast analyst by providing deeper, actionable insights from the existing dataset.
3. **Analyst-Centric Design:** Ensure the page is filled with dense, useful data while maintaining the premium UI/UX aesthetics defined in the Design Constitution.

### R3. Design Constitution & Architecture
The implementation must adhere strictly to the existing Backend Architecture, Design Constitution, and Information Architecture.

## Acceptance Criteria

### Organizational Criteria
- [ ] Every agent performs its clearly defined responsibility without duplicating roles.
- [ ] Every implementation task is accompanied by an Implementation Plan, Task Assignments, Review Findings, and a Final Approval Report.
- [ ] No code is accepted without independent review by the Review Agent.

### Software Quality & Verification Criteria
- [ ] **Agent-as-Judge Verification:** An independent review agent must evaluate the final implementation against a strict rubric:
    - *Filter Functionality:* Do the sub-region, fiscal year, and fiscal quarter filters correctly update the ML vs Manual page without breaking the UI?
    - *Analyst Value:* Does the page feature at least 2 new advanced analytical components that provide concrete value to a forecast analyst?
    - *Aesthetics:* Does the new UI maintain the premium, glassmorphism, cinematic typography design aesthetics?
- [ ] **Data Wiring Verification:** The new dashboard components must be wired to the real backend data (or appropriately extracted via the backend pipeline), not just static mock placeholders.

## Follow-up — 2026-07-13T13:22:56Z

# Teamwork Project Prompt — Draft

Fix the global filter logic in the Enterprise Forecast Decision Intelligence Dashboard so that filters work correctly across all views, and restore the broken Q2 KPI and chart rendering.

Working directory: D:\project_1 imp docs\Forecast review
Integrity mode: demo

## Requirements

### R1. Restore Q2 Functionality
The Q2 page is currently missing KPI values (Champion, Composite Score, Runner-up, Confidence) and the charts are failing to render. The team must identify the regression in `app.js` or the backend data payload and restore the Q2 view to its full operational state.

### R2. Fix Global Filter Logic
The global dropdown filters (Sub-Region, Fiscal Year, Channel) do not function properly across the dashboard. The team must ensure the filters correctly slice the dataset and re-render the charts on all relevant pages without breaking existing layout or components.

## Acceptance Criteria

### Q2 Rendering
- [ ] The Q2 Champion, Composite Score, Runner-up, and Confidence KPIs display correctly populated values from `report.json`.
- [ ] The Q2 Scatter and Boxplot charts render successfully without console errors.

### Global Filters
- [ ] Changing a filter dropdown correctly updates the relevant chart data points (e.g., Q1 WAPE chart, Bias Drift chart) to reflect the filtered subset.
- [ ] The filter state does not cause cascading failures or empty views when switching pages.

## Follow-up — 2026-07-14T01:07:49Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Multi-agent team executing task

Fix the global filter logic in the Enterprise Forecast Decision Intelligence Dashboard so that filters work correctly across all views, and restore the broken Q2 KPI and chart rendering. Additionally, fix missing content in Q1 and Q2, and add more content to Q1 and Q4 as requested by the user.

Working directory: D:\project_1 imp docs\Forecast review
Integrity mode: demo

## Requirements

### R1. Restore Q2 Functionality
The Q2 page is currently missing KPI values (Champion, Composite Score, Runner-up, Confidence) and the charts are failing to render. You must identify the regression in `app.js` or the backend data payload and restore the Q2 view to its full operational state.

### R2. Fix Global Filter Logic
The global dropdown filters (Sub-Region, Fiscal Year, Channel) do not function properly across the dashboard. Ensure the filters correctly slice the dataset and re-render the charts on all relevant pages without breaking existing layout or components. Address the missing `DATA.filters` slice combinations in `report.json` if necessary, or revert the front-end logic to handle data properly.

### R3. Fix Missing Content and Add More Content (Q1, Q2, Q4)
Address missing content bugs in Q1 and Q2 views. Enhance the Q1 and Q4 sections by adding more meaningful content, details, or visualizations as requested. 

## Acceptance Criteria

### Q2 Rendering
- [ ] The Q2 Champion, Composite Score, Runner-up, and Confidence KPIs display correctly populated values from `report.json`.
- [ ] The Q2 Scatter and Boxplot charts render successfully without console errors.
- [ ] Missing content is restored.

### Global Filters
- [ ] Changing a filter dropdown correctly updates the relevant chart data points (e.g., Q1 WAPE chart, Bias Drift chart) to reflect the filtered subset.
- [ ] The filter state does not cause cascading failures or empty views when switching pages.

### Content Enhancements
- [ ] Added more content/details in Q1 and Q4 views.
