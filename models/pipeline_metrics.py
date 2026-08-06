"""
Defines immutable metric objects for tracking pipeline and stage execution times.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class StageTiming:
    """Tracks timing and state for a discrete pipeline stage."""
    stage_name: str
    start_time: float
    end_time: float
    duration_seconds: float
    status: str  # e.g., "SUCCESS", "FAILED", "SKIPPED"
    exception_metadata: Optional[str] = None


@dataclass(frozen=True)
class ExecutionSummary:
    """Summarizes overall pipeline execution status."""
    execution_id: str
    total_duration_seconds: float
    pipeline_status: str
    stages_executed: int
    error_summary: Optional[str] = None


@dataclass(frozen=True)
class PipelineExecutionMetrics:
    """Container for all execution metrics within a pipeline run."""
    execution_summary: ExecutionSummary
    stage_timings: list[StageTiming] = field(default_factory=list)
    
    def as_dict(self) -> dict:
        return {
            "execution_summary": self.execution_summary.__dict__,
            "stage_timings": [stage.__dict__ for stage in self.stage_timings]
        }
