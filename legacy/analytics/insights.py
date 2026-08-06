"""
analytics/insights.py

=========================================================
Module Contract
=========================================================

Purpose
-------
Convert deterministic analytical outputs into structured
business insights for downstream consumption.

Consumes
--------
- Enriched DataFrame from RiskAnalyzer
- Performance outputs
- Comparison outputs
- Drift outputs
- Risk outputs

Produces
--------
DataFrame Columns
    - Forecast_Health
    - Performance_Insight
    - Comparison_Insight
    - Drift_Insight
    - Risk_Insight
    - Executive_Insight

Summary Object
    - InsightSummary

Does NOT
---------
- Calculate performance metrics
- Calculate drift
- Calculate risk
- Generate recommendations
- Call an LLM
- Generate reports

Downstream Consumers
--------------------
- recommendations.py
- review_engine.py
- Executive Summary Generator (LLM)

=========================================================
"""
from __future__ import annotations

import logging
from typing import Tuple, TypedDict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

EXCELLENT = "Excellent"
GOOD = "Good"
NEEDS_ATTENTION = "Needs Attention"
CRITICAL = "Critical"

MANUAL = "Manual"
ML = "ML"
TIE = "Tie"
LOW = "Low"
MEDIUM = "Medium"
HIGH = "High"
STABLE = "Stable"
MODERATE = "Moderate"

EXCELLENT_ACCURACY = 90.0
GOOD_ACCURACY = 70.0
CRITICAL_ACCURACY = 50.0
STABLE_DRIFT = 0.05
HIGH_DRIFT = 0.15
CRITICAL_DRIFT = 0.30
HIGH_CONFIDENCE = 20.0
MEANINGFUL_CONFIDENCE = 5.0

REQUIRED_COLUMNS = (
    "Manual_Accuracy", "ML_Accuracy", "Better_Model",
    "Manual_Drift_Absolute", "ML_Drift_Absolute",
    "Risk_Score", "Risk_Level",
)

OPTIONAL_DEFAULTS: dict[str, object] = {
    "Winner_Confidence": 0.0,
    "Accuracy_Difference": 0.0,
    "Error_Difference": 0.0,
    "Manual_Drift_Category": STABLE,
    "ML_Drift_Category": STABLE,
    "Dominant_Drift_Model": TIE,
    "Risk_Factors": None,
    "Primary_Risk_Driver": "None",
    "Secondary_Risk_Driver": "",
    "Requires_Manager_Review": False,
    "Risk_Confidence": 0.0,
}

OUTPUT_COLUMNS = (
    "Forecast_Health", "Performance_Insight", "Comparison_Insight",
    "Drift_Insight", "Risk_Insight", "Executive_Insight",
)


class InsightSummary(TypedDict):
    """TypedDict for the dataset-level insight summary."""

    overall_forecast_health: str
    overall_model_performance: str
    overall_drift_status: str
    overall_risk_status: str
    critical_forecasts: int
    manager_reviews: int
    top_business_observation: str
    executive_highlight: str


class InsightsAnalyzer:
    """Convert completed analytics into deterministic business observations."""

    def __init__(self) -> None:
        logger.info("InsightsAnalyzer initialized.")

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, InsightSummary]:
        """Generate row-level insights and a dataset-level summary.

        Args:
            dataframe: DataFrame enriched by performance through risk modules.

        Returns:
            Tuple containing the enriched DataFrame and insight summary.

        Raises:
            ValueError: If a required analytical input is missing.
        """

        self._validate_columns(dataframe)
        logger.info(
            "Starting insight synthesis on DataFrame with %d rows", len(dataframe)
        )

        df = dataframe.copy()
        owned_columns = [
            column for column in (*OUTPUT_COLUMNS, "Insight_Factors")
            if column in df.columns
        ]
        if owned_columns:
            logger.info("Replacing existing insight columns: %s", owned_columns)
            df = df.drop(columns=owned_columns)

        missing_optional = [
            column for column in OPTIONAL_DEFAULTS if column not in df.columns
        ]
        if missing_optional:
            logger.warning(
                "Optional insight inputs missing; applying defaults: %s",
                missing_optional,
            )
        for column, default in OPTIONAL_DEFAULTS.items():
            if column not in df.columns:
                if column == "Risk_Factors":
                    df[column] = pd.Series(
                        [[] for _ in range(len(df))], index=df.index, dtype=object
                    )
                else:
                    df[column] = default

        review_values = (
            df["Requires_Manager_Review"].astype("string").str.strip().str.lower()
        )
        df["_Manager_Review"] = review_values.isin(
            {"true", "1", "yes", "y"}
        )

        df = self._generate_insight_factors(df)
        df = self._generate_performance_insight(df)
        df = self._generate_comparison_insight(df)
        df = self._generate_drift_insight(df)
        df = self._generate_risk_insight(df)
        df = self._generate_executive_insight(df)
        summary = self._generate_summary(df)

        df = df.drop(columns=["Insight_Factors", "_Manager_Review"])
        df = df.drop(columns=missing_optional, errors="ignore")
        source_columns = [
            column for column in df.columns if column not in OUTPUT_COLUMNS
        ]
        df = df[[*source_columns, *OUTPUT_COLUMNS]]
        logger.info(
            "Insight synthesis completed: %d critical forecasts; %d manager reviews",
            summary["critical_forecasts"],
            summary["manager_reviews"],
        )
        return df, summary

    def _validate_columns(self, dataframe: pd.DataFrame) -> None:
        """Validate the required upstream analytical contract."""

        missing = [
            column for column in REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]
        if missing:
            raise ValueError(f"Missing required columns for insights: {missing}")

    def _generate_insight_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create internal structured observations and forecast health."""

        manual_accuracy = pd.to_numeric(
            df["Manual_Accuracy"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        ml_accuracy = pd.to_numeric(
            df["ML_Accuracy"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        average_accuracy = pd.concat(
            [manual_accuracy, ml_accuracy], axis=1
        ).mean(axis=1, skipna=True).fillna(0.0).clip(0.0, 100.0)

        manual_drift = pd.to_numeric(
            df["Manual_Drift_Absolute"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        ml_drift = pd.to_numeric(
            df["ML_Drift_Absolute"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        average_drift = pd.concat(
            [manual_drift, ml_drift], axis=1
        ).mean(axis=1, skipna=True).fillna(0.0).clip(lower=0.0)
        risk_score = pd.to_numeric(
            df["Risk_Score"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(0.0, 100.0)
        manager_review = df["_Manager_Review"]

        df["Forecast_Health"] = np.select(
            [
                manager_review | df["Risk_Level"].eq(HIGH),
                df["Risk_Level"].eq(MEDIUM),
            ],
            [CRITICAL, NEEDS_ATTENTION],
            default=GOOD,
        )

        conditions = (
            df["Better_Model"].eq(ML),
            df["Better_Model"].eq(MANUAL),
            df["Better_Model"].eq(TIE),
            average_accuracy >= EXCELLENT_ACCURACY,
            average_accuracy < GOOD_ACCURACY,
            (average_drift > HIGH_DRIFT)
            | df["Manual_Drift_Category"].eq(HIGH)
            | df["ML_Drift_Category"].eq(HIGH),
            average_drift.between(STABLE_DRIFT, HIGH_DRIFT, inclusive="right")
            | df["Manual_Drift_Category"].eq(MODERATE)
            | df["ML_Drift_Category"].eq(MODERATE),
            df["Risk_Level"].eq(HIGH),
            df["Risk_Level"].eq(MEDIUM),
            manager_review,
        )
        names = (
            "ML Outperforming Manual", "Manual Outperforming ML",
            "Models Performing Comparably", "Strong Forecast Accuracy",
            "Low Forecast Accuracy", "High Forecast Drift",
            "Moderate Forecast Drift", "High Risk Forecast",
            "Medium Risk Forecast", "Manager Review Required",
        )
        factor_text = pd.Series("", index=df.index, dtype="string")
        for condition, name in zip(conditions, names):
            factor_text = factor_text.mask(condition, factor_text + name + "; ")
        factor_text = factor_text.str.removesuffix("; ")
        df["Insight_Factors"] = factor_text.str.split("; ").map(
            lambda values: [] if values == [""] else values
        )
        risk_factors = df["Risk_Factors"].map(
            lambda values: values if isinstance(values, list) else []
        )
        df["Insight_Factors"] = df["Insight_Factors"] + risk_factors
        return df

    def _generate_performance_insight(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate deterministic performance observations."""

        factors = df["Insight_Factors"].str.join("|")
        low_accuracy = factors.str.contains("Low Forecast Accuracy", regex=False)
        ml_better = factors.str.contains("ML Outperforming Manual", regex=False)
        manual_better = factors.str.contains("Manual Outperforming ML", regex=False)
        df["Performance_Insight"] = np.select(
            [low_accuracy & ml_better, low_accuracy & manual_better, low_accuracy,
             ml_better, manual_better],
            [
                "ML outperforms Manual, but overall forecast accuracy is low.",
                "Manual outperforms ML, but overall forecast accuracy is low.",
                "Forecast accuracy is below the expected operating threshold.",
                "ML forecasts outperform Manual forecasts.",
                "Manual forecasts outperform ML forecasts.",
            ],
            default="Manual and ML forecast performance is comparable.",
        )
        return df

    def _generate_comparison_insight(self, df: pd.DataFrame) -> pd.DataFrame:
        """Summarize model comparison facts without recalculating them."""

        confidence = pd.to_numeric(
            df["Winner_Confidence"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan).fillna(0.0).abs()
        confidence_label = np.select(
            [confidence >= HIGH_CONFIDENCE,
             confidence >= MEANINGFUL_CONFIDENCE],
            ["clear", "measurable"],
            default="marginal",
        )
        winner = df["Better_Model"].where(
            df["Better_Model"].isin({MANUAL, ML}), TIE
        )
        accuracy_difference = pd.to_numeric(
            df["Accuracy_Difference"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        error_difference = pd.to_numeric(
            df["Error_Difference"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        aligned = (
            winner.eq(ML) & accuracy_difference.ge(0.0)
            & error_difference.ge(0.0)
        ) | (
            winner.eq(MANUAL) & accuracy_difference.le(0.0)
            & error_difference.le(0.0)
        )
        evidence_text = np.where(
            aligned,
            " with aligned accuracy and error differences.",
            " despite mixed accuracy and error differences.",
        )
        df["Comparison_Insight"] = np.where(
            winner.eq(TIE),
            "Manual and ML forecasts have no material performance winner.",
            winner.astype(str) + " holds a " + confidence_label
            + " comparative advantage" + evidence_text,
        )
        return df

    def _generate_drift_insight(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate deterministic forecast-revision observations."""

        factors = df["Insight_Factors"].str.join("|")
        high = factors.str.contains("High Forecast Drift", regex=False)
        moderate = factors.str.contains("Moderate Forecast Drift", regex=False)
        dominant = df["Dominant_Drift_Model"].where(
            df["Dominant_Drift_Model"].isin({MANUAL, ML}), TIE
        )
        df["Drift_Insight"] = np.select(
            [high & dominant.eq(MANUAL), high & dominant.eq(ML), high,
             moderate & dominant.eq(MANUAL), moderate & dominant.eq(ML), moderate],
            [
                "Forecast drift is high and concentrated in the Manual forecast.",
                "Forecast drift is high and concentrated in the ML forecast.",
                "Manual and ML forecasts both show high revision levels.",
                "Forecast drift is moderate and led by the Manual forecast.",
                "Forecast drift is moderate and led by the ML forecast.",
                "Manual and ML forecasts show moderate revision levels.",
            ],
            default="Forecast revisions remain stable.",
        )
        return df

    def _generate_risk_insight(self, df: pd.DataFrame) -> pd.DataFrame:
        """Summarize structured risk facts and review status."""

        level = df["Risk_Level"].where(
            df["Risk_Level"].isin({LOW, MEDIUM, HIGH}), "Unknown"
        ).astype(str)
        primary = df["Primary_Risk_Driver"].fillna("None").astype(str)
        secondary = df["Secondary_Risk_Driver"].fillna("").astype(str)
        driver_text = np.where(
            primary.eq("None"),
            "no material risk driver",
            np.where(
                secondary.ne(""),
                primary + " and " + secondary,
                primary,
            ),
        )
        review_text = np.where(
            df["_Manager_Review"],
            " Manager review is required.",
            "",
        )
        risk_factors = df["Risk_Factors"].map(
            lambda values: values if isinstance(values, list) else []
        ).str.join("; ")
        factor_text = np.where(
            risk_factors.ne(""),
            " Triggered factors: " + risk_factors + ".",
            "",
        )
        df["Risk_Insight"] = (
            level + " forecast risk is driven by "
            + pd.Series(driver_text, index=df.index).str.lower()
            + "." + factor_text + review_text
        )
        return df

    def _generate_executive_insight(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate one concise, non-prescriptive executive observation."""

        factors = df["Insight_Factors"].str.join("|")
        high_drift = factors.str.contains("High Forecast Drift", regex=False)
        low_accuracy = factors.str.contains("Low Forecast Accuracy", regex=False)
        df["Executive_Insight"] = np.select(
            [
                df["Forecast_Health"].eq(CRITICAL) & high_drift,
                df["Forecast_Health"].eq(CRITICAL),
                df["Forecast_Health"].eq(NEEDS_ATTENTION) & low_accuracy,
                df["Forecast_Health"].eq(NEEDS_ATTENTION),
                df["Forecast_Health"].eq(GOOD),
            ],
            [
                "Operational forecasting risk is critical with elevated forecast revisions.",
                "Forecast conditions are critical due to concentrated operational risk.",
                "Forecast quality needs attention because accuracy remains below threshold.",
                "Forecast quality needs attention due to emerging drift or risk signals.",
                "Forecast quality remains healthy with localized analytical concerns.",
            ],
            default="Forecast quality and operational risk remain well controlled.",
        )
        return df

    def _generate_summary(self, df: pd.DataFrame) -> InsightSummary:
        """Aggregate structured observations into a dataset summary."""

        if df.empty:
            return {
                "overall_forecast_health": "No Data",
                "overall_model_performance": "No Data",
                "overall_drift_status": "No Data",
                "overall_risk_status": "No Data",
                "critical_forecasts": 0,
                "manager_reviews": 0,
                "top_business_observation": "",
                "executive_highlight": "",
            }

        normalized_model = df["Better_Model"].where(
            df["Better_Model"].isin({MANUAL, ML, TIE}), TIE
        )
        model_counts = normalized_model.value_counts()
        overall_model = (
            str(model_counts.idxmax()) if not model_counts.empty else TIE
        )
        accuracy_values = pd.concat(
            [pd.to_numeric(df["Manual_Accuracy"], errors="coerce"),
             pd.to_numeric(df["ML_Accuracy"], errors="coerce")], axis=1,
        ).replace([np.inf, -np.inf], np.nan)
        average_accuracy = float(accuracy_values.mean(axis=1).mean())
        drift_values = pd.concat(
            [pd.to_numeric(df["Manual_Drift_Absolute"], errors="coerce"),
             pd.to_numeric(df["ML_Drift_Absolute"], errors="coerce")],
            axis=1,
        ).replace([np.inf, -np.inf], np.nan)
        average_drift = float(drift_values.mean(axis=1).mean())
        risk_values = pd.to_numeric(
            df["Risk_Score"], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        average_risk = float(risk_values.mean())
        manager_reviews = int(df["_Manager_Review"].sum())
        if (
            not np.isfinite(average_accuracy)
            or not np.isfinite(average_risk)
            or not np.isfinite(average_drift)
            or average_risk > 60.0
            or average_accuracy < CRITICAL_ACCURACY
            or average_drift > CRITICAL_DRIFT
        ):
            overall_health = CRITICAL
        elif (
            average_risk > 30.0 or average_accuracy < GOOD_ACCURACY
            or average_drift > HIGH_DRIFT
        ):
            overall_health = NEEDS_ATTENTION
        elif average_accuracy < EXCELLENT_ACCURACY or average_drift > STABLE_DRIFT:
            overall_health = GOOD
        else:
            overall_health = EXCELLENT
        overall_drift = (
            "Unknown" if not np.isfinite(average_drift)
            else HIGH if average_drift > HIGH_DRIFT
            else MODERATE if average_drift > STABLE_DRIFT else STABLE
        )
        overall_risk = (
            "Unknown" if not np.isfinite(average_risk)
            else HIGH if average_risk > 60.0
            else MEDIUM if average_risk > 30.0 else LOW
        )

        observations = df["Insight_Factors"].explode().dropna()
        top_observation = (
            str(observations.value_counts().idxmax())
            if not observations.empty else ""
        )
        executive_highlight = {
            CRITICAL: "Overall forecast health is critical due to aggregate risk, drift, or review signals.",
            NEEDS_ATTENTION: "Overall forecast health needs attention due to elevated analytical signals.",
            GOOD: "Overall forecast health is good with contained analytical concerns.",
            EXCELLENT: "Overall forecast health is excellent with controlled operational risk.",
        }[overall_health]
        summary: InsightSummary = {
            "overall_forecast_health": overall_health,
            "overall_model_performance": overall_model,
            "overall_drift_status": overall_drift,
            "overall_risk_status": overall_risk,
            "critical_forecasts": int(df["Forecast_Health"].eq(CRITICAL).sum()),
            "manager_reviews": manager_reviews,
            "top_business_observation": top_observation,
            "executive_highlight": executive_highlight,
        }
        return summary
