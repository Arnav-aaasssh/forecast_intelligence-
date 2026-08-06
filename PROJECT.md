# Project: Enterprise Forecast Decision Intelligence Platform Dashboard

## Architecture
- **Data Ingestion**: Raw Excel dataset (`sample_data/FinalForecast_Imputed.xlsx`) contains backtest actuals and forecasts for 92 models.
- **Analytics & Decision Engine**: Evaluates models, calculates Wilcoxon sign-rank test, WAPE, Bias, and determines recommended action. Exposes data via FastAPI and static JSON output (`report.json`).
- **Presentation Layer**: Static web dashboard (`dashboard/index.html`, `dashboard/js/app.js`, `dashboard/data/report.json`) rendering interactive charts and leaderboard tables.
- **Data Wiring**: Backend patches `report.json` with processed chart arrays via `generate_dashboard.py`. The frontend fetches `report.json` on page load to dynamically override hardcoded static metrics.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1 | Exploration | Analyze HTML, CSS, JS, and JSON data structures to map filters and dynamic fields. | None | PLANNED |
| M2 | Global Filtering | Move filter bar to global scope, dynamically filter Q1 page charts and metrics on change. | M1 | PLANNED |
| M3 | Advanced Components | Implement Cumulative Bias Drift Chart and Regional/Channel Performance Heatmap Grid. | M2 | PLANNED |
| M4 | UX & Aesthetics | Refine typography, glassmorphism UI, WCAG AA compliance, and derived confidence styling. | M3 | PLANNED |
| M5 | E2E Verification | Run E2E test harness and check with Forensic Auditor to verify data wiring and layout. | M4 | PLANNED |

## Interface Contracts
- **`generate_dashboard.py` ↔ `dashboard/data/report.json`**:
  - `generate_dashboard.py` reads existing `report.json` from the dashboard directory and appends a `chart_data` block containing `q1`, `q2`, `q3`, `q4` metrics and series arrays.
- **`dashboard/js/app.js` ↔ `dashboard/data/report.json`**:
  - `app.js` fetches `data/report.json` asynchronously on `DOMContentLoaded` and maps JSON elements to memory for rendering.

## Code Layout
- `app.py` - CLI entry point.
- `generate_dashboard.py` - Script parsing DataFrame to generate chart arrays for dashboard.
- `dashboard/index.html` - Dashboard presentation layer.
- `dashboard/js/app.js` - Client-side interaction, filtering, and chart rendering logic.
- `dashboard/css/styles.css` - Custom styling conforming to Design Constitution.
- `dashboard/data/report.json` - Combined data report with metrics and chart series.
