"""
comparison.py

Comparison Analysis Module

This module compares Manual and ML forecasts to determine which method
produces lower errors and thus performs better. It enriches the input
DataFrame with comparison metrics and returns summary stats.

Responsibilities
----------------
- Compute row-level comparison between Manual and ML forecasts.
- Generate dataset-level comparison summary.
"""

from __future__ import annotations

import logging
from typing import Tuple, TypedDict

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

MANUAL = "Manual"
ML = "ML"
TIE = "Tie"


class ComparisonSummary(TypedDict):
    """TypedDict for the dataset-level comparison summary."""
    manual_wins: int
    ml_wins: int
    ties: int
    manual_win_rate: float
    ml_win_rate: float
    average_accuracy_difference: float
    average_error_difference: float


class ComparisonAnalyzer:
    """
    Comparison analysis engine.

    Determines which forecasting approach (Manual or ML) performed better for each row,
    and produces overall win/loss statistics.
    """

    def __init__(self) -> None:
        logger.info("ComparisonAnalyzer initialized.")

    def analyze(self, dataframe: pd.DataFrame) -> Tuple[pd.DataFrame, ComparisonSummary]:
        """
        Execute the comparison analysis on the dataset.

        Args:
            dataframe: DataFrame produced by PerformanceAnalyzer (with metrics columns).

        Returns:
            Tuple containing:
            - Enriched DataFrame with new comparison columns.
            - ComparisonSummary dictionary with aggregate stats.
        """
        required_cols = [
            "Manual_Absolute_Error", "ML_Absolute_Error",
            "Manual_Accuracy", "ML_Accuracy"
        ]
        missing = [col for col in required_cols if col not in dataframe.columns]
        if missing:
            raise ValueError(f"Missing required columns for comparison: {missing}")

        logger.info("Starting comparison analysis on DataFrame with %d rows", len(dataframe))
        df = dataframe.copy()

        # Compute row-level comparisons
        df = self._compare_models(df)

        # Generate summary statistics
        summary = self._generate_summary(df)

        logger.info("Comparison analysis completed.")
        return df, summary

    def _compare_models(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compare Manual and ML forecasts at the row level.

        Adds columns:
          Better_Model (Manual/ML/Tie),
          Accuracy_Difference (ML_Accuracy - Manual_Accuracy),
          Error_Difference (Manual_Absolute_Error - ML_Absolute_Error),
          Winner_Confidence (absolute accuracy difference),
          Decision_Reason (why the better model won).
        """
        # Determine which model had lower absolute error (lower error = better)
        manual_lower = df["Manual_Absolute_Error"] < df["ML_Absolute_Error"]
        ml_lower = df["Manual_Absolute_Error"] > df["ML_Absolute_Error"]
        df["Better_Model"] = np.where(
            manual_lower, MANUAL,
            np.where(ml_lower, ML, TIE)
        )

        # Accuracy and error differences
        df["Accuracy_Difference"] = df["ML_Accuracy"] - df["Manual_Accuracy"]
        df["Error_Difference"] = df["Manual_Absolute_Error"] - df["ML_Absolute_Error"]
        df["Winner_Confidence"] = df["Accuracy_Difference"].abs()

        # Decision reason: Tie or lower error
        df["Decision_Reason"] = df["Better_Model"].apply(
            lambda x: "Tie" if x == TIE else "Lower Absolute Error"
        )

        # Log informational summary for historical vs future rows
        if "Actual_Offered" in df.columns:
            future_rows = int(df["Actual_Offered"].isna().sum())
            historical_rows = len(df) - future_rows
        else:
            historical_rows = int(df["Better_Model"].notna().sum())
            future_rows = len(df) - historical_rows
            
        logger.info(
            "Comparison completed on Historical Rows: %d | Future Rows Skipped: %d",
            historical_rows, future_rows
        )

        return df

    def _generate_summary(self, df: pd.DataFrame) -> ComparisonSummary:
        """
        Aggregate comparison results into a summary.
        """
        total = len(df)
        # Count wins and ties
        manual_wins = int((df["Better_Model"] == MANUAL).sum())
        ml_wins = int((df["Better_Model"] == ML).sum())
        ties = int((df["Better_Model"] == TIE).sum())

        # Calculate win rates as percentages
        if total > 0:
            manual_win_rate = (manual_wins / total) * 100.0
            ml_win_rate = (ml_wins / total) * 100.0
        else:
            manual_win_rate = 0.0
            ml_win_rate = 0.0

        # Average differences
        avg_acc_diff = df["Accuracy_Difference"].mean()
        avg_err_diff = df["Error_Difference"].mean()

        summary: ComparisonSummary = {
            "manual_wins": manual_wins,
            "ml_wins": ml_wins,
            "ties": ties,
            "manual_win_rate": manual_win_rate,
            "ml_win_rate": ml_win_rate,
            "average_accuracy_difference": avg_acc_diff,
            "average_error_difference": avg_err_diff
        }
        return summary
