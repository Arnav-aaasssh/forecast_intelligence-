# Plan - Global Filters and Q2 Render Restore

## Objective
Fix the global filter logic in the Enterprise Forecast Decision Intelligence Dashboard so that filters work correctly across all views, restore the broken Q2 KPI and chart rendering, fix missing content in Q1 and Q2, and add more content to Q1 and Q4.

## Milestones

### M1: Exploration & Diagnostics
- **Scope**: Identify why Q2 KPIs and charts are broken. Identify the filter logic bugs. Locate missing content in Q1/Q2 and design content enhancements for Q1/Q4.
- **Verification**: Diagnostic report from Explorer.

### M2: Implementation
- **Scope**: Fix `app.js` and/or `report.json` (or scripts like `generate_dashboard.py` if they build the payload) to:
  - Restore Q2 KPIs and charts.
  - Apply global filter logic across all views properly.
  - Restore missing content in Q1/Q2.
  - Add more content/insights/visualizations in Q1/Q4.
- **Verification**: Build/test commands run by Worker.

### M3: Verification & Integrity Review
- **Scope**: Perform code review and adversarial testing. Run Forensic Audit.
- **Verification**: Reviewer approvals, Challenger checks, Forensic Auditor clean verdict.

### M4: Synthesis & Sentinel Handoff
- **Scope**: Compile the handoff, confirm all acceptance criteria are met, and notify the Sentinel parent.
- **Verification**: Handoff report in teamwork_preview_orchestrator_global_filters_v2 folder.
