"""
Immutable ExecutionContext model carrying execution state through the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable context holding all trace and state information for a single pipeline run.
    """
    execution_id: str
    request_id: str
    run_directory: Path
    started_at: datetime = field(default_factory=datetime.utcnow)
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    
    @property
    def iso_timestamp(self) -> str:
        return self.started_at.isoformat()

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "request_id": self.request_id,
            "run_directory": str(self.run_directory),
            "started_at": self.iso_timestamp,
        }
