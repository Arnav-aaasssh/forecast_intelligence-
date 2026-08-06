# Project: Global Filter Logic and Q2 Restore

## Architecture
- Presentation Layer: HTML dashboard, `dashboard/js/app.js` (large JavaScript client-side application)
- Data Layer: JSON files in `dashboard/data/` (specifically `report.json`)
- Interaction: Dropdown filters for Sub-Region, Fiscal Year, and Channel.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Diagnostic | Investigate the root cause of Q2 KPI and chart rendering issues, and the global filter malfunctioning. | None | DONE |
| 2 | Restore Q2 Functionality | Fix Q2 Champion, Composite Score, Runner-up, and Confidence KPIs, and ensure Scatter and Boxplot charts render. | M1 | IN_PROGRESS |
| 3 | Fix Global Filter Logic | Ensure Sub-Region, Fiscal Year, and Channel filters update relevant charts on all pages without cascading failures. | M2 | IN_PROGRESS |
| 4 | Independent Verification | Review, challenge, and audit the implemented fixes. | M3 | PLANNED |

## Interface Contracts
- The UI filters modify global query state in `app.js`.
- The charts read from sliced data subsets based on global state.
- Data structures in `report.json` must be correctly mapped and filtered in `app.js`.
