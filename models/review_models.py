"""
=========================================================
Module Contract
=========================================================

Purpose
-------
Defines the data contracts used by the Review Engine.

Consumes
--------
Outputs from all analytics modules.

Produces
--------
- PipelineMetadata
- ReviewResult

Does NOT
---------
- Execute analytics
- Perform orchestration
- Read or write files
- Generate reports

Downstream Consumers
--------------------
- services.review_engine
- app.py
- FastAPI
- Power Automate
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd


@dataclass(slots=True)
class RecommendationCard:
    """Structured actionable recommendation."""
    priority: str
    action: str
    reason: str
    category: str


@dataclass(slots=True)
class PipelineMetadata:
    """
    Execution metadata for one complete pipeline run.
    """

    rows_processed: int
    pipeline_status: str
    execution_timestamp: datetime
    modules_executed: list[str] = field(default_factory=list)
    failed_module: str | None = None
    execution_time_seconds: float = 0.0
    execution_id: str | None = None
    reports_dir: str | None = None


@dataclass(slots=True)
class ReviewResult:
    """
    Unified output returned by ReviewEngine.
    """

    dataframe: pd.DataFrame

    validation_summary: dict[str, Any]

    performance_summary: dict[str, Any]

    comparison_summary: dict[str, Any]

    drift_summary: dict[str, Any]

    risk_summary: dict[str, Any]

    insight_summary: dict[str, Any]

    recommendation_summary: dict[str, Any]
    
    top_recommendations: list[RecommendationCard]

    pipeline_metadata: PipelineMetadata