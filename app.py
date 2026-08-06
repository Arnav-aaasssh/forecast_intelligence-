"""
=========================================================
Module Contract
=========================================================

Purpose
-------
Lightweight Application entry point and CLI for the Forecast 
Review & Decision Support System. 

Consumes
--------
- config.settings (configuration constants)
- services.forecast_review_service.ForecastReviewService
- models.review_models.ReviewResult

Produces
--------
- Structured log output with execution summary

Does NOT
--------
- Perform analytics or business calculations
- Generate narrative or call LLMs directly
- Load files or manage DataFrames
- Orchestrate the pipeline directly

Downstream Consumers
---------------------
- None. This is the terminal entry point.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

from config import settings
from models.review_models import ReviewResult
from services.exceptions import DatasetLoadError

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure enterprise structured logging."""
    from utils.logger import configure_enterprise_logging
    configure_enterprise_logging()


def find_default_dataset() -> Path | None:
    """Discover the first supported dataset in the configured input directory.

    Returns:
        Path to the discovered file, or ``None`` if nothing is found.
    """
    input_dir = Path(settings.INPUT_DIRECTORY)
    for ext in settings.SUPPORTED_EXTENSIONS:
        candidates = sorted(input_dir.glob(f"*{ext}"))
        if candidates:
            return candidates[0]
    return None


def _format_row(label: str, value: Any, width: int = 28) -> str:
    """Format a label and value into an aligned row."""
    return f"{label:<{width}} {value}"


def _display_pipeline_status(result: ReviewResult, output_dir: Path) -> list[str]:
    meta = result.pipeline_metadata
    lines = [
        "PIPELINE STATUS",
        "-" * 70,
        _format_row("Pipeline Status", meta.pipeline_status),
        _format_row("Rows Processed", f"{meta.rows_processed:,}"),
        _format_row("Execution Time", f"{meta.execution_time_seconds:.2f} sec"),
        _format_row("Modules Executed", f"{len(meta.modules_executed)} / 7"),
        _format_row("Output Directory", str(output_dir)),
        "",
    ]
    return lines


def _display_forecast_performance(result: ReviewResult) -> list[str]:
    summary = result.performance_summary
    if not summary:
        return []

    lines = [
        "FORECAST PERFORMANCE",
        "-" * 70,
    ]
    manual_acc = summary.get("manual_accuracy")
    ml_acc = summary.get("ml_accuracy")
    winner = summary.get("winner", "Unknown")
    manual_mae = summary.get("manual_mae")
    ml_mae = summary.get("ml_mae")
    manual_mape = summary.get("manual_mape")
    ml_mape = summary.get("ml_mape")

    if manual_acc is not None:
        lines.append(_format_row("Manual Accuracy", f"{manual_acc:.2f}%"))
    if ml_acc is not None:
        lines.append(_format_row("ML Accuracy", f"{ml_acc:.2f}%"))
    if winner:
        lines.append(_format_row("Winning Method", f"{winner} (Based on Lowest MAE)"))
    if manual_mae is not None:
        lines.append(_format_row("Manual MAE", f"{manual_mae:.2f}"))
    if ml_mae is not None:
        lines.append(_format_row("ML MAE", f"{ml_mae:.2f}"))
    if manual_mape is not None:
        lines.append(_format_row("Manual MAPE", f"{manual_mape:.2f}%"))
    if ml_mape is not None:
        lines.append(_format_row("ML MAPE", f"{ml_mape:.2f}%"))

    lines.append("")
    return lines


def _display_risk_overview(result: ReviewResult) -> list[str]:
    summary = result.risk_summary
    if not summary:
        return []

    insights = result.insight_summary or {}
    health = insights.get("overall_forecast_health", "Unknown")

    lines = [
        "RISK OVERVIEW",
        "-" * 70,
        _format_row("Overall Forecast Health", health.upper() if health else "UNKNOWN"),
        _format_row("High Risk Forecasts", f"{summary.get('high_risk_forecasts', 0):,}"),
        _format_row("Medium Risk Forecasts", f"{summary.get('medium_risk_forecasts', 0):,}"),
        _format_row("Low Risk Forecasts", f"{summary.get('low_risk_forecasts', 0):,}"),
        _format_row("Manager Reviews Required", f"{summary.get('manager_reviews_required', 0):,}"),
    ]
    
    highest_score = summary.get("maximum_risk_score")
    if highest_score is not None:
        lines.append(_format_row("Highest Risk Score", f"{highest_score:.2f}"))
        
    average_score = summary.get("average_risk_score")
    if average_score is not None:
        lines.append(_format_row("Average Risk Score", f"{average_score:.2f}"))

    lines.append("")
    return lines


def _display_business_insights(result: ReviewResult) -> list[str]:
    summary = result.insight_summary
    if not summary:
        return []

    lines = [
        "BUSINESS INSIGHTS",
        "-" * 70,
    ]

    crit = summary.get("critical_forecasts")
    if crit is not None:
        lines.append(_format_row("Critical Forecasts", f"{crit:,}"))

    risk_summary = result.risk_summary or {}
    driver = risk_summary.get("top_primary_risk_driver")
    if driver and driver != "None":
        lines.append(_format_row("Top Risk Driver", driver))

    region = risk_summary.get("highest_risk_region")
    if region:
        lines.append(_format_row("Highest Risk Region", region))

    offering = risk_summary.get("highest_risk_offering")
    if offering:
        lines.append(_format_row("Most Volatile Offering", offering))

    lines.append("")
    return lines


def _display_recommendations(result: ReviewResult) -> list[str]:
    df = result.dataframe
    if df is None or "Recommended_Action" not in df.columns:
        return []

    lines = [
        "RECOMMENDED ACTIONS",
        "-" * 70,
    ]

    if "Recommendation_Priority" in df.columns:
        top_actions = []
        for priority in ["Critical", "High", "Medium", "Low"]:
            mask = df["Recommendation_Priority"] == priority
            p_actions = df.loc[mask, "Recommended_Action"].value_counts().index.tolist()
            for a in p_actions:
                if a not in top_actions:
                    top_actions.append(a)
        actions = top_actions
    else:
        actions = df["Recommended_Action"].value_counts().index.tolist()

    for i, action in enumerate(actions[:5], 1):
        lines.append(f"{i}. {action}")

    if not actions:
        lines.append("No specific actions recommended.")

    lines.append("")
    return lines


def _display_system_output(result: ReviewResult, output_dir: Path) -> list[str]:
    meta = result.pipeline_metadata
    lines = [
        "SYSTEM OUTPUT",
        "-" * 70,
        _format_row("Execution Timestamp", meta.execution_timestamp.strftime("%Y-%m-%d %H:%M")),
        _format_row("Reports", str(output_dir)),
        "",
    ]
    return lines


def display_execution_summary(execution, output_dir: Path) -> None:
    """Log a structured executive dashboard summary through the logging system."""
    divider = "=" * 70
    result = execution.review_result

    lines = [
        "",
        divider,
        "           FORECAST REVIEW & DECISION SUPPORT SYSTEM",
        "                    EXECUTIVE REVIEW DASHBOARD",
        divider,
        "",
    ]

    lines.extend(_display_pipeline_status(result, output_dir))
    lines.extend(_display_forecast_performance(result))
    lines.extend(_display_risk_overview(result))
    lines.extend(_display_business_insights(result))
    lines.extend(_display_recommendations(result))
    lines.extend(_display_system_output(result, output_dir))

    lines.extend([
        divider,
        "Pipeline completed successfully." if result.pipeline_metadata.pipeline_status == "SUCCESS" else "Pipeline failed.",
        divider,
    ])

    logger.info("\n" + "\n".join(lines))


def main(input_path: Path | None = None) -> int:
    """Application CLI entry point.

    Args:
        input_path: Path to the forecast dataset.  Falls back to the
            first supported file found in the configured input directory.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    app_start = perf_counter()
    configure_logging()
    logger.info("Application Started via CLI.")

    resolved_input = input_path or find_default_dataset()

    if resolved_input is None:
        logger.error(
            "No input file provided and no datasets found in %s.",
            settings.INPUT_DIRECTORY,
        )
        return 1

    try:
        from services.service_registry import create_forecast_review_service
        service = create_forecast_review_service()
        execution = service.run(resolved_input)
        
        try:
            import generate_dashboard
            generate_dashboard.generate_dashboard_data(execution.review_result.dataframe)
        except Exception as e:
            logger.error("Failed to generate dashboard chart data: %s", e)
            
        # Safely resolve the reports directory for the summary display
        _pm = getattr(execution, 'pipeline_metadata', None)
        _reports_dir = getattr(_pm, 'reports_dir', None) if _pm else None
        if _reports_dir is None:
            _reports_dir = Path(settings.OUTPUT_DIRECTORY)
        display_execution_summary(execution, _reports_dir)

    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        return 1
    except DatasetLoadError as exc:
        logger.error("Dataset load error: %s", exc)
        return 1
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        return 1

    app_elapsed = perf_counter() - app_start
    logger.info("Application Finished. Total wall-clock time: %.4fs", app_elapsed)
    return 0


if __name__ == "__main__":
    cli_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(main(input_path=cli_path))
