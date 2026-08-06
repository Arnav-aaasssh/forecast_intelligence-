"""Validation services for incoming forecast datasets.

The validator checks a loaded :class:`pandas.DataFrame` against the Forecast
Review Dataset contract. It performs no analytics, reporting, narrative
generation, or recommendation logic.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from time import perf_counter
from typing import Any, Callable, ClassVar, Literal, Mapping

import pandas as pd
from pandas.api import types as pandas_types

from config import settings
from models.validation_models import ValidationIssue, ValidationReport
from services.exceptions import ConfigurationError, ValidationRuntimeError

logger = logging.getLogger(__name__)

Severity = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]


class DatasetValidator:
    """Validate an incoming forecast dataset against its data contract.

    The supplied DataFrame is copied so validation defaults never mutate the
    caller's object. After a successful run, ``validated_dataset`` provides a
    defensive copy containing any configured default replacements.

    Args:
        dataset: Loaded forecast dataset. ``None`` represents a load failure.
        defaults: Missing-value replacements. When omitted, the documented
            ``Holiday_Count`` default of zero is used. Pass an empty mapping to
            disable all defaults. Defaults cannot override fields whose missing
            value strategy requires rejection.
        duplicate_severity: Configurable severity level for duplicate detection.
            Defaults to "WARNING". Use "ERROR" for strict production ingestion.
    """

    EXPECTED_DTYPES: ClassVar[Mapping[str, str]] = settings.EXPECTED_DTYPES
    DEFAULT_VALUES: ClassVar[Mapping[str, Any]] = settings.DEFAULT_VALUES
    FORECAST_COLUMNS: ClassVar[tuple[str, ...]] = settings.FORECAST_COLUMNS
    DUPLICATE_KEY_COLUMNS: ClassVar[tuple[str, ...]] = settings.DUPLICATE_KEY_COLUMNS

    # --- NEW VALIDATION CONTRACT RULES ---
    MANDATORY_COLUMNS: ClassVar[tuple[str, ...]] = (
        "Forecast_Name", "Model", "Family", "Fiscal_Year", "Week_Ending",
        "Fiscal_Week", "Month_Number", "Week_Number", "Country", "Region",
        "Offering", "Channel", "Forecaster", 
        "ML_Forecast", "Mean (Hist. Contacts) (Last 1 yr.)",
        "Std Dev (Hist. Contacts)"
    )

    BUSINESS_NULLABLE_COLUMNS: ClassVar[tuple[str, ...]] = (
        "Actual_Offered", "Actual_ASU", "Manual_Forecast", "Previous_Forecast", "Final_upp_units",
        "SubRegion", "Planned_ASU", "Volume_Category", "Holiday_Count"
    )

    BOOLEAN_COLUMNS: ClassVar[tuple[str, ...]] = (
        "Manual_±10%", "ML_±10%", "ML≥Manual_or_±10%"
    )

    _SUPPORTED_DTYPES: ClassVar[frozenset[str]] = frozenset(
        {"String", "Integer", "Float", "Boolean", "Datetime"}
    )

    # --- SEVERITY MAPPING ---
    # Centralized rules configuration for easy maintenance
    RULE_SEVERITY: ClassVar[Mapping[str, Severity]] = {
        "missing_mandatory": "ERROR",
        "missing_nullable_schema": "WARNING",
        "duplicate_columns": "ERROR",
        "invalid_dtype": "ERROR",
        "invalid_boolean": "ERROR",
        "invalid_fiscal_week": "ERROR",
        "negative_forecast": "ERROR",
        "invalid_month": "ERROR",
        "missing_actuals": "WARNING",
        "missing_manual": "WARNING",
        "missing_previous": "WARNING",
        "missing_other_nullable": "WARNING",
        "applied_default": "INFO",
        # duplicate_records uses instance-level configuration
    }

    def __init__(
        self,
        dataset: pd.DataFrame | None,
        defaults: Mapping[str, Any] | None = None,
        duplicate_severity: Severity = "WARNING",
    ) -> None:
        self._validate_configuration()
        self._source_is_dataframe = isinstance(dataset, pd.DataFrame)
        self._source_dataset = (
            dataset.copy(deep=True) if self._source_is_dataframe else None
        )
        self._dataset = (
            self._source_dataset.copy(deep=True)
            if self._source_dataset is not None
            else None
        )
        self._defaults = dict(
            self.DEFAULT_VALUES if defaults is None else defaults
        )
        self._duplicate_severity = duplicate_severity
        self._warnings: list[ValidationIssue] = []
        self._errors: list[ValidationIssue] = []
        self._infos: list[ValidationIssue] = []
        
        now = datetime.now(timezone.utc)
        self._validation_start = now
        self._validation_end = now
        self._execution_time_seconds = 0.0

    @property
    def validated_dataset(self) -> pd.DataFrame | None:
        """Return a defensive copy of the dataset with defaults applied."""
        if self._dataset is None:
            return None
        return self._dataset.copy(deep=True)

    def validate_dataset(self) -> ValidationReport:
        """Run the complete staged validation workflow."""

        started_at = datetime.now(timezone.utc)
        started_counter = perf_counter()
        self._start_validation(started_at)

        if not self._source_is_dataframe or self._dataset is None:
            self._add_error(
                "VAL-001",
                "Dataset was not loaded successfully as a pandas DataFrame.",
                severity="CRITICAL",
                suggested_cause="The data file is corrupted or unsupported."
            )
            return self._finish_validation(started_counter)

        if self._dataset.empty:
            self._add_error(
                "VAL-002", 
                "Dataset is empty.",
                severity="ERROR",
                suggested_cause="Empty extract pulled from data source."
            )
            return self._finish_validation(started_counter)

        try:
            # Stage 1: Schema
            self.validate_schema()
            if self._errors:
                return self._finish_validation(started_counter)

            # Stage 2: DataTypes
            self.validate_dtypes()
            if self._errors:
                return self._finish_validation(started_counter)

            # Stage 3: Business Rules
            self.validate_business_rules()
            if self._errors:
                return self._finish_validation(started_counter)

            # Stage 4: Data Quality & Missing Values
            self.validate_data_quality()
            
        except Exception as exc:
            self._validation_end = datetime.now(timezone.utc)
            self._execution_time_seconds = perf_counter() - started_counter
            logger.exception("Runtime Exception", extra=self._log_context())
            if isinstance(exc, ValidationRuntimeError):
                raise
            raise ValidationRuntimeError(
                "Unexpected runtime error during dataset validation."
            ) from exc

        return self._finish_validation(started_counter)

    def validate_schema(self) -> None:
        """Validate required and unexpected dataset columns."""
        if self._dataset is None:
            return

        available = set(self._dataset.columns)
        
        # 1. Mandatory Columns
        missing_mandatory = [col for col in self.MANDATORY_COLUMNS if col not in available]
        if missing_mandatory:
            self._add_issue(
                self.RULE_SEVERITY["missing_mandatory"],
                "VAL-101",
                "Mandatory columns are missing.",
                affected_columns=missing_mandatory,
                suggested_cause="Source extract is missing required dimensional fields."
            )

        # 2. Business Nullable Columns
        missing_nullable = [col for col in self.BUSINESS_NULLABLE_COLUMNS if col not in available]
        if missing_nullable:
            self._add_issue(
                self.RULE_SEVERITY["missing_nullable_schema"],
                "VAL-102",
                "Business-nullable columns are completely missing from the schema.",
                affected_columns=missing_nullable,
                suggested_cause="Target forecast columns were omitted from the extract."
            )

        # 3. Duplicate Columns
        duplicate_columns = [
            str(column) for column in self._dataset.columns[
                self._dataset.columns.duplicated(keep=False)
            ].unique()
        ]
        if duplicate_columns:
            self._add_issue(
                self.RULE_SEVERITY["duplicate_columns"],
                "VAL-103",
                "Duplicate column names were found.",
                affected_columns=duplicate_columns,
                suggested_cause="SQL JOIN issue or malformed Excel header."
            )

    def validate_dtypes(self) -> None:
        """Validate values against expected business semantics and dtypes."""
        if self._dataset is None:
            return

        skip_strict_dtypes = set(self.BOOLEAN_COLUMNS) | {"RISK Flag (w/ Holiday)", "Fiscal_Week"}
        
        for column, expected_type in self.EXPECTED_DTYPES.items():
            if column not in self._dataset.columns:
                continue
            if int((self._dataset.columns == column).sum()) > 1:
                continue
            if column in skip_strict_dtypes:
                continue
                
            series = self._dataset[column]
            if not self._matches_expected_type(series, expected_type):
                self._add_issue(
                    self.RULE_SEVERITY["invalid_dtype"],
                    "VAL-201",
                    f"Column '{column}' does not match expected business type '{expected_type}'.",
                    affected_columns=[column],
                    suggested_cause="Incorrect parsing or mixed data types in the column."
                )

    def validate_business_rules(self) -> None:
        """Apply forecasting domain business rules."""
        if self._dataset is None:
            return

        # 1. Boolean Indicators
        valid_bools = {True, False, 1, 0, 1.0, 0.0, "True", "False", "true", "false", "1", "0", "1.0", "0.0"}
        for col in self.BOOLEAN_COLUMNS:
            if col in self._dataset.columns:
                series = self._dataset[col]
                missing = self._missing_mask(series)
                non_null_series = series.loc[~missing]
                invalid = ~non_null_series.isin(valid_bools)
                count = int(invalid.sum())
                if count:
                    self._add_issue(
                        self.RULE_SEVERITY["invalid_boolean"],
                        "VAL-301",
                        f"Column '{col}' contains values that cannot represent boolean information.",
                        affected_columns=[col],
                        affected_rows=count,
                        suggested_cause="Invalid boolean serialization from source (e.g., float NaNs or unstructured text)."
                    )

        # 2. Fiscal Week Encoding
        col = "Fiscal_Week"
        if col in self._dataset.columns:
            series = pd.to_numeric(self._dataset[col], errors="coerce")
            missing_numeric = series.isna() & self._dataset[col].notna()
            str_series = self._dataset[col].astype(str).str.strip()
            invalid_len = (str_series.str.replace(r'\.0$', '', regex=True).str.len() != 6) & self._dataset[col].notna()
            week_num = series % 100
            invalid_week = (~week_num.between(1, 53)) & series.notna()
            invalid = missing_numeric | invalid_len | invalid_week
            count = int(invalid.sum())
            if count:
                self._add_issue(
                    self.RULE_SEVERITY["invalid_fiscal_week"],
                    "VAL-302",
                    f"Column '{col}' contains invalid enterprise encoded values.",
                    affected_columns=[col],
                    affected_rows=count,
                    suggested_cause="Values must be numeric 6-digit encoded weeks (e.g., 202706)."
                )

        # 3. Numeric constraints (Forecast values >= 0)
        cols_to_check = list(self.FORECAST_COLUMNS) + ["Actual_Offered"]
        for col in cols_to_check:
            if col in self._dataset.columns:
                values = pd.to_numeric(self._dataset[col], errors="coerce")
                invalid = (values < 0) & values.notna()
                count = int(invalid.sum())
                if count:
                    self._add_issue(
                        self.RULE_SEVERITY["negative_forecast"],
                        "VAL-303",
                        f"Forecast column '{col}' cannot contain negative values.",
                        affected_columns=[col],
                        affected_rows=count,
                        suggested_cause="Mathematical error in upstream system."
                    )

        # Month constraints
        if "Month_Number" in self._dataset.columns:
            values = pd.to_numeric(self._dataset["Month_Number"], errors="coerce")
            invalid = (~values.between(1, 12)) & values.notna()
            count = int(invalid.sum())
            if count:
                self._add_issue(
                    self.RULE_SEVERITY["invalid_month"],
                    "VAL-304",
                    "Month_Number must be between 1 and 12.",
                    affected_columns=["Month_Number"],
                    affected_rows=count,
                    suggested_cause="Date dimension error."
                )

    def validate_data_quality(self) -> None:
        """Validate missing values according to severity classifications."""
        if self._dataset is None:
            return

        # 1. Mandatory Columns (ERROR if missing)
        for col in self.MANDATORY_COLUMNS:
            if col in self._dataset.columns:
                missing = self._missing_mask(self._dataset[col])
                count = int(missing.sum())
                if count:
                    self._add_issue(
                        self.RULE_SEVERITY["missing_mandatory"],
                        "VAL-401",
                        f"Mandatory column '{col}' contains missing values.",
                        affected_columns=[col],
                        affected_rows=count,
                        suggested_cause="Source data extraction failed to populate mandatory dimension."
                    )

        # 2. Business Nullable Columns
        for col in self.BUSINESS_NULLABLE_COLUMNS:
            if col in self._dataset.columns:
                missing = self._missing_mask(self._dataset[col])
                count = int(missing.sum())
                if count:
                    if col == "Actual_Offered":
                        self._add_issue(
                            self.RULE_SEVERITY["missing_actuals"],
                            "VAL-402",
                            f"Column '{col}' contains missing values. These may be expected for future forecast periods.",
                            affected_columns=[col],
                            affected_rows=count,
                            suggested_cause="Historical/future classification is not currently available, so no rejection was performed."
                        )
                    elif col == "Manual_Forecast":
                        self._add_issue(
                            self.RULE_SEVERITY["missing_manual"],
                            "VAL-403",
                            f"Manual forecasts are missing for {count} rows.",
                            affected_columns=[col],
                            affected_rows=count,
                            suggested_cause="This may indicate forecasts were not submitted for certain products, regions, or forecast cycles."
                        )
                    elif col == "Previous_Forecast":
                        self._add_issue(
                            self.RULE_SEVERITY["missing_previous"],
                            "VAL-404",
                            "Previous forecast unavailable.",
                            affected_columns=[col],
                            affected_rows=count,
                            suggested_cause="This is expected for new products, new regions, or the first forecasting cycle."
                        )
                    else:
                        self._add_issue(
                            self.RULE_SEVERITY["missing_other_nullable"],
                            "VAL-405",
                            f"Business-nullable column '{col}' contains missing values.",
                            affected_columns=[col],
                            affected_rows=count,
                            suggested_cause="May be expected based on the specific phase of the forecast lifecycle."
                        )

        # 3. Apply Defaults
        for col, default in self._defaults.items():
            if col not in self._dataset.columns:
                continue
            if col in self.MANDATORY_COLUMNS:
                continue # Defaults shouldn't override mandatory missing errors
            missing = self._missing_mask(self._dataset[col])
            count = int(missing.sum())
            if count:
                self._dataset.loc[missing, col] = default
                self._add_issue(
                    self.RULE_SEVERITY["applied_default"],
                    "VAL-406",
                    f"Applied default value {default!r} to missing values.",
                    affected_columns=[col],
                    affected_rows=count,
                    suggested_cause="Standard missing-value imputation."
                )

        # 4. Duplicates
        if all(col in self._dataset.columns for col in self.DUPLICATE_KEY_COLUMNS):
            duplicate_mask = self._dataset.duplicated(subset=list(self.DUPLICATE_KEY_COLUMNS), keep=False)
            duplicate_rows = int(duplicate_mask.sum())
            if duplicate_rows:
                duplicate_groups = int(self._dataset.loc[duplicate_mask].groupby(list(self.DUPLICATE_KEY_COLUMNS), dropna=False).ngroups)
                self._add_issue(
                    self._duplicate_severity,
                    "VAL-407",
                    f"Detected {duplicate_rows} rows across {duplicate_groups} duplicate forecast-record groups.",
                    affected_rows=duplicate_rows,
                    suggested_cause="Multiple submissions or overlapping queries."
                )

    def generate_report(self) -> ValidationReport:
        rows, columns = self._dataset_dimensions()
        
        if self._errors:
            status = "FAILED"
        elif self._warnings:
            status = "SUCCESS_WITH_WARNINGS"
        else:
            status = "SUCCESS"
            
        return ValidationReport(
            status=status,
            rows=rows,
            columns=columns,
            validation_start=self._validation_start,
            validation_end=self._validation_end,
            execution_time_seconds=self._execution_time_seconds,
            rows_processed=rows,
            columns_processed=columns,
            warnings=list(self._warnings),
            errors=list(self._errors),
            infos=list(self._infos)
        )

    def _start_validation(self, started_at: datetime) -> None:
        self._warnings = []
        self._errors = []
        self._infos = []
        self._dataset = self._copy_source_dataset()
        self._validation_start = started_at
        self._validation_end = started_at
        self._execution_time_seconds = 0.0
        rows, columns = self._dataset_dimensions()
        logger.info("Validation Started")

    def _finish_validation(self, started_counter: float) -> ValidationReport:
        self._validation_end = datetime.now(timezone.utc)
        self._execution_time_seconds = perf_counter() - started_counter
        report = self.generate_report()
        
        # Build formatted report exactly to specification
        lines = [
            "",
            "=" * 52,
            "VALIDATION REPORT",
            "=" * 52,
            "Status",
            report.status,
            "Errors",
            str(len(report.errors)),
            "Warnings",
            str(len(report.warnings)),
        ]
        
        for issue in report.warnings:
            lines.extend([
                "-" * 52,
                "WARNING",
                issue.affected_columns[0] if issue.affected_columns else "Dataset",
                f"{issue.affected_rows} missing values" if issue.affected_rows else issue.message,
                issue.suggested_cause or "",
            ])
            
        for issue in report.errors:
            lines.extend([
                "-" * 52,
                "ERROR",
                issue.affected_columns[0] if issue.affected_columns else "Dataset",
                f"{issue.affected_rows} invalid values" if issue.affected_rows else issue.message,
                issue.suggested_cause or "",
            ])

        lines.extend([
            "=" * 52,
            "Validation Completed Successfully" if report.status in ("SUCCESS", "SUCCESS_WITH_WARNINGS") else "Validation Failed",
            "=" * 52,
        ])
        
        logger.info("\n".join(lines))
        
        return report

    def _log_context(self) -> dict[str, int | float | str]:
        rows, columns = self._dataset_dimensions()
        return {
            "status": "FAILED" if self._errors else "SUCCESS",
            "rows": rows,
            "columns": columns,
            "execution_time_seconds": self._execution_time_seconds,
            "warning_count": len(self._warnings),
            "error_count": len(self._errors),
            "info_count": len(self._infos),
        }

    def _copy_source_dataset(self) -> pd.DataFrame | None:
        if self._source_dataset is None:
            return None
        return self._source_dataset.copy(deep=True)

    def _dataset_dimensions(self) -> tuple[int, int]:
        if self._dataset is None:
            return 0, 0
        return len(self._dataset.index), len(self._dataset.columns)

    @classmethod
    def _validate_configuration(cls) -> None:
        unsupported = set(cls.EXPECTED_DTYPES.values()) - cls._SUPPORTED_DTYPES
        if unsupported:
            raise ConfigurationError(
                "Unsupported configured data types: "
                + ", ".join(sorted(unsupported))
                + "."
            )

    @staticmethod
    def _matches_expected_type(series: pd.Series, expected_type: str) -> bool:
        non_null = series.loc[~DatasetValidator._missing_mask(series)]
        if non_null.empty:
            return True

        if expected_type == "String":
            return bool(non_null.map(lambda value: isinstance(value, str)).all())
        if expected_type == "Integer":
            if pandas_types.is_bool_dtype(series.dtype):
                return False
            if not pandas_types.is_numeric_dtype(series.dtype):
                return False
            return bool((non_null % 1 == 0).all())
        if expected_type == "Float":
            return bool(
                pandas_types.is_numeric_dtype(series.dtype)
                and not pandas_types.is_bool_dtype(series.dtype)
            )
        if expected_type == "Boolean":
            return bool(
                pandas_types.is_bool_dtype(series.dtype)
                or pandas_types.infer_dtype(non_null, skipna=True) == "boolean"
            )
        if expected_type == "Datetime":
            if pandas_types.is_datetime64_any_dtype(series.dtype):
                return True
            return bool(
                non_null.map(
                    lambda value: isinstance(value, (date, datetime, pd.Timestamp))
                ).all()
            )
        raise ConfigurationError(f"Unsupported expected data type: {expected_type}")

    @staticmethod
    def _missing_mask(series: pd.Series) -> pd.Series:
        mask = series.isna()
        if pandas_types.is_object_dtype(series.dtype) or pandas_types.is_string_dtype(series.dtype):
            blank = series.astype("string").str.strip().eq("").fillna(False)
            mask = mask | blank
        return mask

    def _add_issue(
        self,
        severity: Severity,
        code: str,
        message: str,
        affected_columns: list[str] | None = None,
        affected_rows: int | None = None,
        suggested_cause: str | None = None,
    ) -> None:
        """Centralized helper for logging an issue to the correct collection."""
        issue = ValidationIssue(
            code=code, 
            severity=severity, 
            message=message,
            affected_columns=affected_columns or [],
            affected_rows=affected_rows,
            suggested_cause=suggested_cause
        )
        if severity == "INFO":
            if issue not in self._infos:
                self._infos.append(issue)
        elif severity == "WARNING":
            if issue not in self._warnings:
                self._warnings.append(issue)
        else: # ERROR or CRITICAL
            if issue not in self._errors:
                self._errors.append(issue)

    def _add_info(self, *args, **kwargs) -> None:
        """Deprecated: Use _add_issue instead."""
        self._add_issue("INFO", *args, **kwargs)

    def _add_warning(self, *args, **kwargs) -> None:
        """Deprecated: Use _add_issue instead."""
        self._add_issue("WARNING", *args, **kwargs)

    def _add_error(self, *args, **kwargs) -> None:
        """Deprecated: Use _add_issue instead."""
        self._add_issue("ERROR", *args, **kwargs)
