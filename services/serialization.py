"""
Shared serialization logic for the Forecast Review system.

Provides the single source of truth for converting a ReviewResult into the canonical JSON dictionary schema,
used by both the JSON Report Generator and the FastAPI presentation layer.
"""

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings
from models.review_models import RecommendationCard
from models.execution_models import ForecastReviewExecution


def serialize_review_result(execution: ForecastReviewExecution) -> dict[str, Any]:
    """
    Constructs the stable JSON schema dictionary from the complete execution record.
    
    Args:
        execution: The complete ForecastReviewExecution record.
                    
    Returns:
        The canonical JSON dictionary representation.
    """
    result = execution.review_result
    meta = result.pipeline_metadata
    
    # 1. Gracefully extract recommendations
    actions: list[dict[str, Any]] = []
    if getattr(result, "top_recommendations", None):
        for rec in result.top_recommendations:
            if isinstance(rec, RecommendationCard):
                actions.append(asdict(rec))
            else:
                actions.append(rec)  # Fallback if it's already a dict

    # 2. Extract execution metadata
    pipeline_status = meta.pipeline_status if meta else "UNKNOWN"
    failed_module = meta.failed_module if meta else None
    
    artifacts_dir = str(execution.html_report_path.parent.absolute()) if execution.html_report_path else str(Path(settings.OUTPUT_DIRECTORY).absolute())

    validation_summary = result.validation_summary or {}
    warnings = validation_summary.get("warnings", 0)
    errors = validation_summary.get("errors", 1 if failed_module else 0)
    
    if isinstance(warnings, list):
        warnings = len(warnings)
    elif isinstance(warnings, str) and warnings.isdigit():
        warnings = int(warnings)
        
    if isinstance(errors, list):
        errors = len(errors)
    elif isinstance(errors, str) and errors.isdigit():
        errors = int(errors)
        
    validation_status = validation_summary.get("status", "PASS" if pipeline_status == "SUCCESS" else "FAIL")

    rec_summary = dict(result.recommendation_summary) if result.recommendation_summary else {}
    if "top_recommendations" in rec_summary:
        rec_summary["top_recommendations"] = [
            asdict(r) if hasattr(r, "__dataclass_fields__") else r
            for r in rec_summary["top_recommendations"]
        ]

    # 3. Assemble Schema
    schema = {
        "metadata": {
            "schema_version": getattr(settings, "REPORT_SCHEMA_VERSION", "1.0"),
            "application_version": getattr(settings, "APP_VERSION", "Unknown"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": getattr(settings, "APP_NAME", "Forecast Review System"),
            "environment": getattr(settings, "APP_ENVIRONMENT", "development")
        },
        "pipeline": {
            "execution_id": meta.execution_id if meta else getattr(execution, "execution_id", None),
            "status": pipeline_status,
            "execution_time_seconds": meta.execution_time_seconds if meta else 0.0,
            "total_execution_duration": getattr(execution, "execution_duration", 0.0),
            "rows_processed": meta.rows_processed if meta else 0,
            "modules_executed": meta.modules_executed if meta and meta.modules_executed else [],
            "failed_module": failed_module
        },
        "validation": {
            "status": validation_status,
            "warnings": warnings,
            "errors": errors
        },
        "performance": result.performance_summary or {},
        "comparison": result.comparison_summary or {},
        "risk": result.risk_summary or {},
        "insights": result.insight_summary or {},
        "recommendations": {
            "summary": rec_summary,
            "actions": actions
        },
        "artifacts": {
            "directory": artifacts_dir,
            "html": execution.html_report_path.name if execution.html_report_path else "forecast_review.html",
            "json": execution.json_report_path.name if execution.json_report_path else getattr(settings, "JSON_REPORT_NAME", "forecast_review.json"),
            "executive_summary": execution.executive_summary_path.name if execution.executive_summary_path else "executive_summary.md",
            "manager_summary": execution.manager_summary_path.name if execution.manager_summary_path else "manager_summary.md",
            "email_summary": execution.email_summary_path.name if execution.email_summary_path else "email_summary.md",
            "teams_summary": execution.teams_summary_path.name if execution.teams_summary_path else "teams_summary.md"
        }
    }
    
    return schema
