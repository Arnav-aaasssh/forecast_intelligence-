"""Compute deterministic forecast risk intelligence."""

from __future__ import annotations

import logging
from typing import Tuple, TypedDict

import numpy as np
import pandas as pd

from core import metrics

logger = logging.getLogger(__name__)

ACCURACY_WEIGHT = 0.40
DRIFT_WEIGHT = 0.25
VOLATILITY_WEIGHT = 0.15
HOLIDAY_WEIGHT = 0.10
BUSINESS_RISK_WEIGHT = 0.10

LOW_RISK_MAX = 30.0
MEDIUM_RISK_MAX = 60.0
LOW_ACCURACY_THRESHOLD = 70.0
HIGH_DRIFT_THRESHOLD = 0.15
LARGE_REVISION_THRESHOLD = 0.30
VOLATILITY_THRESHOLD = 0.50
DEMAND_INSTABILITY_THRESHOLD = 1.00
HOLIDAY_RISK_PER_DAY = 25.0
MAX_COMPONENT_SCORE = 100.0

LOW = "Low"
MEDIUM = "Medium"
HIGH = "High"
MANUAL = "Manual"
ML = "ML"
TIE = "Tie"
NO_DRIVER = "None"
NO_SECONDARY_DRIVER = ""

ACCURACY_DRIVER = "Forecast Accuracy"
DRIFT_DRIVER = "Forecast Drift"
VOLATILITY_DRIVER = "Historical Volatility"
HOLIDAY_DRIVER = "Holiday Impact"
BUSINESS_DRIVER = "Business Risk Flag"

RISK_FLAG_COLUMN = "RISK Flag (w/ Holiday)"
RISK_CATEGORY_COLUMN = "RISK Cat (w/ Holiday)"
HISTORICAL_MEAN_COLUMN = "Mean (Hist. Contacts) (Last 1 yr.)"
HISTORICAL_STD_COLUMN = "Std Dev (Hist. Contacts)"

REQUIRED_COLUMNS = (
    "Manual_Accuracy", "ML_Accuracy", "Better_Model",
    "Manual_Drift_Absolute", "ML_Drift_Absolute", "Holiday_Count",
    RISK_FLAG_COLUMN, RISK_CATEGORY_COLUMN, HISTORICAL_MEAN_COLUMN,
    HISTORICAL_STD_COLUMN, "Region", "Offering", "Channel",
)

OUTPUT_COLUMNS = (
    "Risk_Score", "Risk_Level", "Primary_Risk_Driver",
    "Secondary_Risk_Driver", "Risk_Factors", "Risk_Reason",
    "Requires_Manager_Review", "Risk_Confidence",
)

COMPONENT_COLUMNS = (
    "_Accuracy_Risk", "_Drift_Risk", "_Volatility_Risk",
    "_Holiday_Risk", "_Business_Risk",
)

CONTRIBUTION_COLUMNS = (
    "_Accuracy_Contribution", "_Drift_Contribution",
    "_Volatility_Contribution", "_Holiday_Contribution",
    "_Business_Contribution",
)

DRIVER_NAMES = np.array(
    [ACCURACY_DRIVER, DRIFT_DRIVER, VOLATILITY_DRIVER,
     HOLIDAY_DRIVER, BUSINESS_DRIVER],
    dtype=object,
)


class RiskSummary(TypedDict):
    """TypedDict for the dataset-level risk summary."""

    average_risk_score: float
    maximum_risk_score: float
    minimum_risk_score: float
    high_risk_forecasts: int
    medium_risk_forecasts: int
    low_risk_forecasts: int
    manager_reviews_required: int
    top_primary_risk_driver: str
    average_confidence: float
    highest_risk_region: str
    highest_risk_offering: str
    highest_risk_channel: str


class RiskAnalyzer:
    """Convert upstream analytical facts into structured risk intelligence."""

    def __init__(self, metrics_module=metrics) -> None:
        """Initialize with an injectable metrics module for testing."""

        self.metrics = metrics_module
        logger.info(
            "RiskAnalyzer initialized with metrics module %s", metrics_module
        )

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, RiskSummary]:
        """Return the enriched DataFrame and dataset-level risk summary.

        Args:
            dataframe: Enriched DataFrame produced by upstream analytics.

        Raises:
            ValueError: If inputs are missing or outputs already exist.
        """

        self._validate_columns(dataframe)
        logger.info(
            "Starting risk analysis on DataFrame with %d rows", len(dataframe)
        )

        df = dataframe.copy()
        df = self._calculate_risk_score(df)
        df = self._assign_risk_level(df)
        df = self._identify_risk_factors(df)
        df = self._generate_risk_reason(df)
        summary = self._generate_summary(df)
        df = df.drop(columns=[*COMPONENT_COLUMNS, *CONTRIBUTION_COLUMNS])
        source_columns = [
            column for column in df.columns if column not in OUTPUT_COLUMNS
        ]
        df = df[[*source_columns, *OUTPUT_COLUMNS]]

        logger.info(
            "Risk analysis completed: %d high-risk forecasts; %d manager "
            "reviews required",
            summary["high_risk_forecasts"],
            summary["manager_reviews_required"],
        )
        return df, summary

    def _validate_columns(self, dataframe: pd.DataFrame) -> None:
        """Validate inputs and protect owned output columns."""

        missing = [
            column for column in REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]
        if missing:
            raise ValueError(f"Missing required columns for risk: {missing}")

        existing = [
            column for column in OUTPUT_COLUMNS
            if column in dataframe.columns
        ]
        if existing:
            raise ValueError(
                "Risk output columns already exist and cannot be overwritten: "
                f"{existing}"
            )

    def _calculate_risk_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate normalized components, contributions, and total risk."""

        manual_accuracy = pd.to_numeric(
            df["Manual_Accuracy"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        ml_accuracy = pd.to_numeric(
            df["ML_Accuracy"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        best_accuracy = np.fmax(manual_accuracy, ml_accuracy).fillna(MAX_COMPONENT_SCORE)
        df["_Accuracy_Risk"] = (
            MAX_COMPONENT_SCORE - best_accuracy
        ).clip(0.0, MAX_COMPONENT_SCORE)

        manual_drift = pd.to_numeric(
            df["Manual_Drift_Absolute"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        ml_drift = pd.to_numeric(
            df["ML_Drift_Absolute"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        maximum_drift = np.fmax(manual_drift, ml_drift).fillna(0.0).clip(lower=0.0)
        df["_Drift_Risk"] = (
            maximum_drift * MAX_COMPONENT_SCORE
        ).clip(0.0, MAX_COMPONENT_SCORE)

        historical_mean = pd.to_numeric(
            df[HISTORICAL_MEAN_COLUMN], errors="coerce"
        ).to_numpy(dtype=float)
        historical_std = pd.to_numeric(
            df[HISTORICAL_STD_COLUMN], errors="coerce"
        ).to_numpy(dtype=float)
        valid_history = (
            np.isfinite(historical_mean)
            & np.isfinite(historical_std)
            & (historical_mean != 0.0)
        )
        volatility = np.zeros(len(df), dtype=float)
        numerator = np.zeros(len(df), dtype=float)
        np.abs(historical_std, out=numerator, where=valid_history)
        denominator = np.where(valid_history, np.abs(historical_mean), 1.0)
        volatility = np.asarray(
            self.metrics.safe_divide(numerator, denominator), dtype=float
        )
        zero_mean_with_variation = (
            np.isfinite(historical_std)
            & (historical_mean == 0.0)
            & (historical_std != 0.0)
        )
        volatility[zero_mean_with_variation] = 1.0
        volatility = np.nan_to_num(
            volatility, nan=0.0, posinf=1.0, neginf=0.0
        )
        df["_Volatility_Risk"] = np.clip(
            volatility * MAX_COMPONENT_SCORE, 0.0, MAX_COMPONENT_SCORE
        )

        holiday_count = pd.to_numeric(
            df["Holiday_Count"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(lower=0.0)
        df["_Holiday_Risk"] = (
            holiday_count * HOLIDAY_RISK_PER_DAY
        ).clip(0.0, MAX_COMPONENT_SCORE)

        flag_values = df[RISK_FLAG_COLUMN].astype("string").str.strip().str.lower()
        category_values = (
            df[RISK_CATEGORY_COLUMN].astype("string").str.strip().str.lower()
        )
        flag_triggered = flag_values.isin(
            {"1", "true", "yes", "y", "high", "critical", "flagged"}
        )
        category_triggered = category_values.isin({"high", "critical"})
        df["_Business_Risk"] = (
            (flag_triggered | category_triggered).astype(float)
            * MAX_COMPONENT_SCORE
        )

        weights = (
            ACCURACY_WEIGHT,
            DRIFT_WEIGHT,
            VOLATILITY_WEIGHT,
            HOLIDAY_WEIGHT,
            BUSINESS_RISK_WEIGHT,
        )
        for component, contribution, weight in zip(
            COMPONENT_COLUMNS, CONTRIBUTION_COLUMNS, weights
        ):
            df[contribution] = df[component] * weight

        df["Risk_Score"] = (
            df[list(CONTRIBUTION_COLUMNS)].sum(axis=1)
            .clip(0.0, MAX_COMPONENT_SCORE)
        )
        return df

    def _assign_risk_level(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign risk levels, drivers, and management-review flags."""

        df["Risk_Level"] = np.select(
            [
                df["Risk_Score"] <= LOW_RISK_MAX,
                df["Risk_Score"] <= MEDIUM_RISK_MAX,
            ],
            [LOW, MEDIUM],
            default=HIGH,
        )
        df["Requires_Manager_Review"] = df["Risk_Level"] == HIGH

        contributions = df[list(CONTRIBUTION_COLUMNS)].to_numpy(dtype=float)
        if len(df):
            ranked_indices = np.argsort(
                -contributions, axis=1, kind="stable"
            )
            primary = DRIVER_NAMES[ranked_indices[:, 0]]
            secondary = DRIVER_NAMES[ranked_indices[:, 1]]
            no_risk = np.isclose(contributions.sum(axis=1), 0.0)
            secondary_absent = np.isclose(
                np.take_along_axis(
                    contributions, ranked_indices[:, 1:2], axis=1
                ).ravel(),
                0.0,
            )
            df["Primary_Risk_Driver"] = np.where(
                no_risk, NO_DRIVER, primary
            )
            df["Secondary_Risk_Driver"] = np.where(
                no_risk | secondary_absent, NO_SECONDARY_DRIVER, secondary
            )
        else:
            df["Primary_Risk_Driver"] = pd.Series(dtype="object")
            df["Secondary_Risk_Driver"] = pd.Series(dtype="object")

        return df

    def _identify_risk_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify triggered conditions and calculate risk confidence."""

        best_accuracy = MAX_COMPONENT_SCORE - df["_Accuracy_Risk"]
        maximum_drift = df["_Drift_Risk"] / MAX_COMPONENT_SCORE
        volatility = df["_Volatility_Risk"] / MAX_COMPONENT_SCORE

        conditions = (
            maximum_drift > HIGH_DRIFT_THRESHOLD,
            best_accuracy < LOW_ACCURACY_THRESHOLD,
            volatility >= VOLATILITY_THRESHOLD,
            df["_Holiday_Risk"] > 0.0,
            df["_Business_Risk"] > 0.0,
            df["Better_Model"].eq(ML), df["Better_Model"].eq(MANUAL),
            maximum_drift >= LARGE_REVISION_THRESHOLD,
            volatility >= DEMAND_INSTABILITY_THRESHOLD,
        )
        factor_names = (
            "High Forecast Drift", "Low Forecast Accuracy",
            "Historical Volatility", "Holiday Impact", "Business Risk Flag",
            "Manual Forecast Underperforming", "ML Forecast Underperforming",
            "Large Forecast Revision", "Demand Instability",
        )

        factor_text = pd.Series("", index=df.index, dtype="string")
        for condition, factor_name in zip(conditions, factor_names):
            factor_text = factor_text.mask(
                condition,
                factor_text + factor_name + "; ",
            )
        factor_text = factor_text.str.removesuffix("; ")
        df["Risk_Factors"] = factor_text.str.split("; ").map(
            lambda values: [] if values == [""] else values
        )

        independent_indicators = np.column_stack(
            [
                conditions[1],
                conditions[0],
                conditions[2],
                conditions[3],
                conditions[4],
            ]
        )
        df["Risk_Confidence"] = (
            independent_indicators.mean(axis=1) * MAX_COMPONENT_SCORE
            if len(df)
            else np.array([], dtype=float)
        )
        return df

    def _generate_risk_reason(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build deterministic reasons from triggered risk factors."""

        df["Risk_Reason"] = df["Risk_Factors"].str.join("; ")
        return df

    def _generate_summary(self, df: pd.DataFrame) -> RiskSummary:
        """Aggregate row-level risk intelligence into a dataset summary."""

        if df.empty:
            return {
                "average_risk_score": 0.0,
                "maximum_risk_score": 0.0,
                "minimum_risk_score": 0.0,
                "high_risk_forecasts": 0,
                "medium_risk_forecasts": 0,
                "low_risk_forecasts": 0,
                "manager_reviews_required": 0,
                "top_primary_risk_driver": NO_DRIVER,
                "average_confidence": 0.0,
                "highest_risk_region": "",
                "highest_risk_offering": "",
                "highest_risk_channel": "",
            }

        primary_drivers = df.loc[
            df["Primary_Risk_Driver"] != NO_DRIVER,
            "Primary_Risk_Driver",
        ]
        top_driver = (
            str(primary_drivers.value_counts(sort=True).index[0])
            if not primary_drivers.empty
            else NO_DRIVER
        )

        highest_groups: dict[str, str] = {}
        for column in ("Region", "Offering", "Channel"):
            valid_groups = df[column].notna()
            grouped_scores = (
                df.loc[valid_groups]
                .groupby(column, sort=True, dropna=True)["Risk_Score"]
                .mean()
            )
            highest_groups[column] = (
                str(grouped_scores.idxmax()) if not grouped_scores.empty else ""
            )

        summary: RiskSummary = {
            "average_risk_score": float(df["Risk_Score"].mean()),
            "maximum_risk_score": float(df["Risk_Score"].max()),
            "minimum_risk_score": float(df["Risk_Score"].min()),
            "high_risk_forecasts": int((df["Risk_Level"] == HIGH).sum()),
            "medium_risk_forecasts": int((df["Risk_Level"] == MEDIUM).sum()),
            "low_risk_forecasts": int((df["Risk_Level"] == LOW).sum()),
            "manager_reviews_required": int(
                df["Requires_Manager_Review"].sum()
            ),
            "top_primary_risk_driver": top_driver,
            "average_confidence": float(df["Risk_Confidence"].mean()),
            "highest_risk_region": highest_groups["Region"],
            "highest_risk_offering": highest_groups["Offering"],
            "highest_risk_channel": highest_groups["Channel"],
        }
        return summary
