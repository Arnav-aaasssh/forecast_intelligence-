# analytics/performance.py

from typing import Tuple, Dict, TypedDict
import logging

import pandas as pd

from core import metrics

logger = logging.getLogger(__name__)


class PerformanceSummary(TypedDict):
    """TypedDict for the dataset-level performance summary."""
    manual_accuracy: float
    ml_accuracy: float
    manual_mae: float
    ml_mae: float
    manual_mape: float
    ml_mape: float
    manual_bias: float
    ml_bias: float
    manual_adherence: float
    ml_adherence: float
    manual_within_10_pct: float
    ml_within_10_pct: float
    winner: str


class PerformanceAnalyzer:
    """
    Performance analysis engine.

    Processes a validated forecast DataFrame to compute row-level performance metrics
    and overall summary statistics. Does NOT produce reports or recommendations.
    """

    def __init__(self, metrics_module=metrics) -> None:
        """
        Args:
            metrics_module: Module providing metric functions (for DI/testing).
        """
        self.metrics = metrics_module
        logger.info("PerformanceAnalyzer initialized with metrics module %s", metrics_module)

    def analyze(self, dataframe: pd.DataFrame) -> Tuple[pd.DataFrame, PerformanceSummary]:
        """
        Compute performance metrics for the dataset.

        Args:
            dataframe: Validated forecast DataFrame with required columns.

        Returns:
            Tuple of:
            - Enriched DataFrame (with new metric columns added)
            - PerformanceSummary TypedDict with aggregate stats.
        """
        required_cols = [
            "Manual_Forecast", "ML_Forecast", "Actual_Offered",
            "Manual_Adh", "ML_Adh", "Manual_±10%", "ML_±10%"
        ]
        # Validate input columns
        missing = [col for col in required_cols if col not in dataframe.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        logger.info("Starting performance analysis on DataFrame with %d rows", len(dataframe))
        df = dataframe.copy()  # Work on a copy to avoid side-effects

        # Calculate row-level metrics
        df = self._calculate_row_metrics(df)

        # Generate summary statistics
        summary = self._generate_summary(df)

        logger.info("Performance analysis completed.")
        return df, summary

    def _calculate_row_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate and append row-level forecast metrics.

        Adds columns: Manual_Error, ML_Error, Manual_Absolute_Error, ML_Absolute_Error,
        Manual_Accuracy, ML_Accuracy.
        """
        # Compute errors
        df["Manual_Error"] = self.metrics.calculate_error(df["Manual_Forecast"], df["Actual_Offered"])
        df["ML_Error"] = self.metrics.calculate_error(df["ML_Forecast"], df["Actual_Offered"])

        # Compute absolute errors
        df["Manual_Absolute_Error"] = self.metrics.calculate_absolute_error(df["Manual_Forecast"], df["Actual_Offered"])
        df["ML_Absolute_Error"] = self.metrics.calculate_absolute_error(df["ML_Forecast"], df["Actual_Offered"])

        # Compute accuracies
        df["Manual_Accuracy"] = self.metrics.calculate_accuracy(df["Manual_Forecast"], df["Actual_Offered"])
        df["ML_Accuracy"] = self.metrics.calculate_accuracy(df["ML_Forecast"], df["Actual_Offered"])

        # Log informational summary for historical vs future rows
        historical_rows = int(df["Actual_Offered"].notna().sum())
        future_rows = int(df["Actual_Offered"].isna().sum())
        logger.info(
            "Performance metrics computed on Historical Rows: %d | Future Rows Skipped: %d",
            historical_rows, future_rows
        )

        return df

    def _generate_summary(self, df: pd.DataFrame) -> PerformanceSummary:
        """
        Aggregate row metrics into a performance summary.
        """
        # Use skipna=True by default for mean(), effectively ignoring NaNs.
        manual_accuracy = df["Manual_Accuracy"].mean()
        ml_accuracy = df["ML_Accuracy"].mean()
        manual_mae = df["Manual_Absolute_Error"].mean()
        ml_mae = df["ML_Absolute_Error"].mean()

        # MAPE: use core.metrics if available, else compute from series
        try:
            manual_mape = self.metrics.calculate_mape(df["Manual_Forecast"], df["Actual_Offered"])
            ml_mape = self.metrics.calculate_mape(df["ML_Forecast"], df["Actual_Offered"])
        except AttributeError:
            # Fallback: compute manually, avoid division by zero
            manual_mape = (abs(df["Manual_Error"] / df["Actual_Offered"])).mean() * 100
            ml_mape = (abs(df["ML_Error"] / df["Actual_Offered"])).mean() * 100

        # Bias: average signed error
        manual_bias = df["Manual_Error"].mean()
        ml_bias = df["ML_Error"].mean()

        # Adherence: average of the provided adherence fractions
        manual_adherence = df["Manual_Adh"].mean()
        ml_adherence = df["ML_Adh"].mean()

        # Within-10%: fraction of rows where indicator == 1.0
        manual_within = df["Manual_±10%"].mean() * 100  # multiply by 100 for percentage
        ml_within = df["ML_±10%"].mean() * 100

        # Determine winner: simple rule, compare average MAE (or any business rule)
        winner = "Manual" if manual_mae < ml_mae else "ML"

        # Build the summary TypedDict
        summary: PerformanceSummary = {
            "manual_accuracy": manual_accuracy,
            "ml_accuracy": ml_accuracy,
            "manual_mae": manual_mae,
            "ml_mae": ml_mae,
            "manual_mape": manual_mape,
            "ml_mape": ml_mape,
            "manual_bias": manual_bias,
            "ml_bias": ml_bias,
            "manual_adherence": manual_adherence,
            "ml_adherence": ml_adherence,
            "manual_within_10_pct": manual_within,
            "ml_within_10_pct": ml_within,
            "winner": winner
        }
        return summary
