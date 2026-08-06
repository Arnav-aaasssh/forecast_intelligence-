"""Typed response models for forecast dataset validation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ValidationSeverity = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
ValidationStatus = Literal["SUCCESS", "SUCCESS_WITH_WARNINGS", "FAILED"]


class ValidationIssue(BaseModel):
    """Describe one validation finding with a stable code and severity."""

    code: str = Field(pattern=r"^VAL-\d{3}$")
    severity: ValidationSeverity
    message: str
    affected_columns: list[str] = Field(default_factory=list)
    affected_rows: int | None = None
    suggested_cause: str | None = None


class ValidationReport(BaseModel):
    """Represent the complete, JSON-serializable validation result."""

    status: ValidationStatus
    rows: int = Field(ge=0)
    columns: int = Field(ge=0)
    validation_start: datetime
    validation_end: datetime
    execution_time_seconds: float = Field(ge=0)
    rows_processed: int = Field(ge=0)
    columns_processed: int = Field(ge=0)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    errors: list[ValidationIssue] = Field(default_factory=list)
    infos: list[ValidationIssue] = Field(default_factory=list)
