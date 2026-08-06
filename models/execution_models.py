"""
=========================================================
Module Contract
=========================================================

Purpose
-------
Defines the higher-level execution contracts representing an entire pipeline run.

Consumes
--------
- models.review_models.ReviewResult

Produces
--------
- ForecastReviewExecution

Does NOT
---------
- Execute analytics
- Perform orchestration
- Read or write files
- Generate reports
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.review_models import ReviewResult


@dataclass(slots=True, frozen=True)
class ForecastReviewExecution:
    """
    Immutable model representing a complete application execution,
    including the analytics result and all generated artifact paths.
    """

    review_result: ReviewResult = field(repr=False)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    html_report_path: Optional[Path] = None
    json_report_path: Optional[Path] = None
    executive_summary_path: Optional[Path] = None
    manager_summary_path: Optional[Path] = None
    email_summary_path: Optional[Path] = None
    teams_summary_path: Optional[Path] = None

    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_duration: float = 0.0
    pipeline_status: str = "UNKNOWN"
