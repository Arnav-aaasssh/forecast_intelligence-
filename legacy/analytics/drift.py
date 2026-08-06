"""Measure Manual and ML forecast drift from the approved prior forecast."""

from __future__ import annotations

import logging
from typing import Tuple, TypedDict

import numpy as np
import pandas as pd

from core import metrics

logger = logging.getLogger(__name__)

STABLE_THRESHOLD = 0.05
MODERATE_THRESHOLD = 0.15

STABLE = "Stable"
MODERATE = "Moderate"
HIGH = "High"
MANUAL = "Manual"
ML = "ML"
TIE = "Tie"

REQUIRED_COLUMNS = (
    "Manual_Forecast",
    "ML_Forecast",
    "Previous_Forecast",
    "Actual_Offered",
)

OUTPUT_COLUMNS = (
    "Manual_Drift",
    "ML_Drift",
    "Manual_Drift_Absolute",
    "ML_Drift_Absolute",
    "Manual_Drift_Category",
    "ML_Drift_Category",
    "Manual_Drift_Flag",
    "ML_Drift_Flag",
    "Drift_Difference",
    "Dominant_Drift_Model",
)


class DriftSummary(TypedDict):
    """TypedDict for the dataset-level forecast drift summary."""

    average_manual_drift: float
    average_ml_drift: float
    average_manual_absolute_drift: float
    average_ml_absolute_drift: float
    maximum_manual_drift: float
    maximum_ml_drift: float
    stable_manual_forecasts: int
    stable_ml_forecasts: int
    moderate_manual_forecasts: int
    moderate_ml_forecasts: int
    high_manual_forecasts: int
    high_ml_forecasts: int


class DriftAnalyzer:
    """Forecast drift analysis engine.

    Measures Manual and ML forecast revisions relative to the previously
    approved forecast and produces aggregate drift statistics. The supplied
    DataFrame is never mutated.
    """

    def __init__(self, metrics_module=metrics) -> None:
        """Initialize the analyzer.

        Args:
            metrics_module: Module providing metric functions (for DI/testing).
        """

        self.metrics = metrics_module
        logger.info(
            "DriftAnalyzer initialized with metrics module %s", metrics_module
        )

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, DriftSummary]:
        """Compute forecast drift metrics for the dataset.

        Args:
            dataframe: Enriched forecast DataFrame with required forecast
                columns.

        Returns:
            Tuple containing:
            - Enriched DataFrame with drift columns appended.
            - DriftSummary dictionary with aggregate statistics.

        Raises:
            ValueError: If required columns are missing.
        """

        self._validate_columns(dataframe)
        logger.info(
            "Starting drift analysis on DataFrame with %d rows", len(dataframe)
        )

        df = dataframe.copy()
        df = self._calculate_drift(df)
        df = self._classify_drift(df)
        summary = self._generate_summary(df)

        logger.info("Drift analysis completed.")
        return df, summary

    def _validate_columns(self, dataframe: pd.DataFrame) -> None:
        """Validate the input column contract.

        Args:
            dataframe: DataFrame to validate.

        Raises:
            ValueError: If required columns are absent.
        """

        missing = [
            column for column in REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]
        if missing:
            raise ValueError(f"Missing required columns for drift: {missing}")

    def _calculate_drift(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate signed and absolute Manual and ML forecast drift.

        Invalid numeric values and zero previous forecasts produce neutral
        drift values of zero, consistent with the shared safe-divide behavior.

        Args:
            df: Copied DataFrame containing the required forecast columns.

        Returns:
            DataFrame with signed and absolute drift columns appended.
        """

        previous = pd.to_numeric(
            df["Previous_Forecast"], errors="coerce"
        ).to_numpy(dtype=float)
        calculated_drift: dict[str, np.ndarray] = {}

        for model in ("Manual", "ML"):
            forecast = pd.to_numeric(
                df[f"{model}_Forecast"], errors="coerce"
            ).to_numpy(dtype=float)
            valid = (
                np.isfinite(forecast)
                & np.isfinite(previous)
                & (previous != 0.0)
            )
            invalid_count = int((~valid).sum())
            if invalid_count:
                logger.warning(
                    "%s drift defaulted to zero for %d rows with invalid "
                    "forecast or previous forecast values",
                    model,
                    invalid_count,
                )
            numerator = np.zeros_like(forecast, dtype=float)
            np.subtract(forecast, previous, out=numerator, where=valid)
            denominator = np.where(valid, previous, 1.0)
            drift = self.metrics.safe_divide(numerator, denominator)
            drift = np.nan_to_num(
                np.asarray(drift, dtype=float),
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

            calculated_drift[model] = drift

        for model in ("Manual", "ML"):
            df[f"{model}_Drift"] = calculated_drift[model]
        for model in ("Manual", "ML"):
            df[f"{model}_Drift_Absolute"] = np.abs(
                calculated_drift[model]
            )

        return df

    def _classify_drift(self, df: pd.DataFrame) -> pd.DataFrame:
        """Classify absolute drift and set review flags.

        Args:
            df: DataFrame containing calculated drift values.

        Returns:
            DataFrame with category and flag columns appended.
        """

        categories: dict[str, np.ndarray] = {}
        for model in ("Manual", "ML"):
            absolute_drift = df[f"{model}_Drift_Absolute"]
            categories[model] = np.select(
                [
                    absolute_drift <= STABLE_THRESHOLD,
                    absolute_drift <= MODERATE_THRESHOLD,
                ],
                [STABLE, MODERATE],
                default=HIGH,
            )

        for model in ("Manual", "ML"):
            df[f"{model}_Drift_Category"] = categories[model]
        for model in ("Manual", "ML"):
            df[f"{model}_Drift_Flag"] = categories[model] != STABLE

        df["Drift_Difference"] = (
            df["Manual_Drift_Absolute"] - df["ML_Drift_Absolute"]
        )
        df["Dominant_Drift_Model"] = np.select(
            [df["Drift_Difference"] > 0.0, df["Drift_Difference"] < 0.0],
            [MANUAL, ML],
            default=TIE,
        )

        return df

    def _generate_summary(self, df: pd.DataFrame) -> DriftSummary:
        """Aggregate row-level drift values into a dataset summary.

        Args:
            df: DataFrame containing calculated and classified drift values.

        Returns:
            Dataset-level drift statistics. Numeric aggregates are zero for an
            empty DataFrame.
        """

        manual_drift = df["Manual_Drift"]
        ml_drift = df["ML_Drift"]
        manual_absolute = df["Manual_Drift_Absolute"]
        ml_absolute = df["ML_Drift_Absolute"]

        summary: DriftSummary = {
            "average_manual_drift": self.metrics.safe_mean(manual_drift),
            "average_ml_drift": self.metrics.safe_mean(ml_drift),
            "average_manual_absolute_drift": self.metrics.safe_mean(
                manual_absolute
            ),
            "average_ml_absolute_drift": self.metrics.safe_mean(ml_absolute),
            "maximum_manual_drift": (
                float(manual_absolute.max()) if not df.empty else 0.0
            ),
            "maximum_ml_drift": (
                float(ml_absolute.max()) if not df.empty else 0.0
            ),
            "stable_manual_forecasts": int((df["Manual_Drift_Category"] == STABLE).sum()),
            "stable_ml_forecasts": int((df["ML_Drift_Category"] == STABLE).sum()),
            "moderate_manual_forecasts": int((df["Manual_Drift_Category"] == MODERATE).sum()),
            "moderate_ml_forecasts": int((df["ML_Drift_Category"] == MODERATE).sum()),
            "high_manual_forecasts": int((df["Manual_Drift_Category"] == HIGH).sum()),
            "high_ml_forecasts": int((df["ML_Drift_Category"] == HIGH).sum()),
        }
        return summary
