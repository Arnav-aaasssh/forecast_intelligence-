"""
Module Contract
===============

Purpose:
    Convert deterministic business insights into deterministic business actions.

Consumes:
    - Forecast health and insight outputs
    - Structured risk outputs and manager-review indicators

Produces:
    - Recommendation priority, category, action, reason, owner, and confidence
    - RecommendationSummary

Does NOT:
    - Recalculate analytics or risk
    - Generate insights or reports
    - Call an LLM

Downstream Consumers:
    - review_engine.py
    - LLM narrative generation
"""

from __future__ import annotations

import logging
from typing import Tuple, TypedDict

import pandas as pd

logger = logging.getLogger(__name__)

LOW = "Low"
MEDIUM = "Medium"
HIGH = "High"
CRITICAL = "Critical"

PRIORITY_RANK = {LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3}
RANK_PRIORITY = {rank: priority for priority, rank in PRIORITY_RANK.items()}
RISK_PRIORITY_RULES = {HIGH: CRITICAL, MEDIUM: HIGH, LOW: LOW}
HEALTH_PRIORITY_RULES = {
    CRITICAL: CRITICAL,
    "Needs Attention": HIGH,
    "Good": MEDIUM,
    "Excellent": LOW,
}

OWNER_RULES = {
    "Forecast Review": "Forecast Analyst",
    "Demand Validation": "Demand Planner",
    "Capacity Planning": "Regional Manager",
    "Staffing Review": "Regional Manager",
    "Executive Review": "Executive Management",
    "Data Quality": "Forecast Governance Team",
    "Business Validation": "Regional Manager",
}

CATEGORY_RULES = (
    ("Manager Review", "Executive Review"),
    ("Data Quality Issue", "Data Quality"),
    ("Staffing Risk", "Staffing Review"),
    ("Capacity Constraint", "Capacity Planning"),
    ("Holiday Impact", "Demand Validation"),
    ("Demand Instability", "Demand Validation"),
    ("Historical Volatility", "Business Validation"),
    ("Business Risk Flag", "Business Validation"),
    ("High Forecast Drift", "Forecast Review"),
    ("Large Forecast Revision", "Forecast Review"),
    ("Low Forecast Accuracy", "Forecast Review"),
    ("Manual Forecast Underperforming", "Forecast Review"),
    ("ML Forecast Underperforming", "Forecast Review"),
)

ACTION_FACTOR_RULES = (
    ("Manager Review", "Escalate for executive approval."),
    ("Data Quality Issue", "Validate source data quality."),
    ("Staffing Risk", "Review staffing assumptions."),
    ("Capacity Constraint", "Review capacity assumptions."),
    ("High Forecast Drift", "Investigate forecast revisions."),
    ("Large Forecast Revision", "Investigate forecast revisions."),
    ("Holiday Impact", "Validate demand drivers."),
    ("Demand Instability", "Validate demand drivers."),
    ("Historical Volatility", "Validate historical demand."),
    ("Business Risk Flag", "Validate business risk conditions."),
    ("Low Forecast Accuracy", "Review forecast assumptions."),
    ("Manual Forecast Underperforming", "Review forecast assumptions."),
    ("ML Forecast Underperforming", "Review forecast assumptions."),
)

CATEGORY_ACTION_RULES = {
    "Forecast Review": "Review forecast assumptions.",
    "Demand Validation": "Validate demand drivers.",
    "Capacity Planning": "Review capacity assumptions.",
    "Staffing Review": "Review staffing assumptions.",
    "Executive Review": "Escalate for executive approval.",
    "Data Quality": "Validate source data quality.",
    "Business Validation": "Validate business conditions.",
}

REASON_RULES = {
    "Manager Review": "Manager review is required due to elevated operational risk",
    "High Risk": "Forecast risk is high",
    "Medium Risk": "Forecast risk is elevated",
    "Critical Forecast Health": "Forecast health is critical",
    "Forecast Needs Attention": "Forecast health needs attention",
    "High Forecast Drift": "Forecast revisions are high",
    "Large Forecast Revision": "A large forecast revision is present",
    "Low Forecast Accuracy": "Forecast accuracy is below threshold",
    "Historical Volatility": "Historical demand is volatile",
    "Demand Instability": "Demand patterns are unstable",
    "Holiday Impact": "Holiday effects are present",
    "Business Risk Flag": "An existing business risk is flagged",
    "Manual Forecast Underperforming": "Manual forecasting is underperforming",
    "ML Forecast Underperforming": "ML forecasting is underperforming",
    "Data Quality Issue": "Analytical evidence indicates a data-quality issue",
    "Capacity Constraint": "Capacity constraints are present",
    "Staffing Risk": "Staffing risk is present",
    "Low Risk": "Forecast risk remains low",
    "Good Forecast Health": "Forecast health remains good",
    "Excellent Forecast Health": "Forecast health remains excellent",
}

REQUIRED_COLUMNS = (
    "Forecast_Health",
    "Risk_Level",
    "Requires_Manager_Review",
)

OPTIONAL_DEFAULTS: dict[str, object] = {
    "Risk_Factors": None,
}

OUTPUT_COLUMNS = (
    "Recommendation_Priority",
    "Recommended_Action",
    "Recommendation_Category",
    "Recommendation_Reason",
    "Recommended_Owner",
    "Recommendation_Confidence",
)


class RecommendationSummary(TypedDict):
    """TypedDict for the dataset-level recommendation summary."""

    critical_recommendations: int
    high_priority_recommendations: int
    medium_priority_recommendations: int
    low_priority_recommendations: int
    manager_reviews_required: int
    top_recommendation_category: str
    top_recommended_owner: str
    highest_confidence: float
    average_confidence: float
    top_recommendations: list[Any]


class RecommendationAnalyzer:
    """Convert structured business observations into deterministic actions."""

    def __init__(self) -> None:
        logger.info("RecommendationAnalyzer initialized.")

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, RecommendationSummary]:
        """Generate recommendations and a dataset-level summary.

        Args:
            dataframe: DataFrame enriched by the insights module.

        Returns:
            Tuple containing the enriched DataFrame and recommendation summary.

        Raises:
            ValueError: If a required insight or risk input is missing.
        """

        self._validate_columns(dataframe)
        logger.info(
            "Starting recommendation analysis on DataFrame with %d rows",
            len(dataframe),
        )
        df = dataframe.copy()
        owned = [
            column for column in (*OUTPUT_COLUMNS, "Decision_Factors")
            if column in df.columns
        ]
        if owned:
            logger.info("Replacing existing recommendation columns: %s", owned)
            df = df.drop(columns=owned)

        missing_optional = [
            column for column in OPTIONAL_DEFAULTS if column not in df.columns
        ]
        if missing_optional:
            logger.warning(
                "Optional recommendation inputs missing; applying defaults: %s",
                missing_optional,
            )
        for column, default in OPTIONAL_DEFAULTS.items():
            if column not in df.columns:
                df[column] = (
                    pd.Series(
                        [[] for _ in range(len(df))],
                        index=df.index,
                        dtype=object,
                    )
                    if column == "Risk_Factors"
                    else default
                )

        review_values = (
            df["Requires_Manager_Review"].astype("string").str.strip().str.lower()
        )
        df["_Manager_Review"] = review_values.isin(
            {"true", "1", "yes", "y"}
        )
        df = self._generate_decision_factors(df)
        df = self._assign_priority(df)
        df = self._assign_category(df)
        df = self._generate_recommendation(df)
        df = self._assign_owner(df)
        df = self._generate_reason(df)
        summary = self._generate_summary(df)

        df = df.drop(columns=["Decision_Factors", "_Manager_Review"])
        df = df.drop(columns=missing_optional, errors="ignore")
        source_columns = [
            column for column in df.columns if column not in OUTPUT_COLUMNS
        ]
        df = df[[*source_columns, *OUTPUT_COLUMNS]]
        logger.info(
            "Recommendation analysis completed: %d critical; %d high priority",
            summary["critical_recommendations"],
            summary["high_priority_recommendations"],
        )
        return df, summary

    def _validate_columns(self, dataframe: pd.DataFrame) -> None:
        """Validate required upstream decision inputs."""

        missing = [
            column for column in REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]
        if missing:
            raise ValueError(
                f"Missing required columns for recommendations: {missing}"
            )

    def _generate_decision_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build the internal structured evidence used by all decisions."""

        risk_factor = df["Risk_Level"].map(
            {HIGH: "High Risk", MEDIUM: "Medium Risk", LOW: "Low Risk"}
        ).fillna("Unknown Risk")
        health_factor = df["Forecast_Health"].map(
            {
                CRITICAL: "Critical Forecast Health",
                "Needs Attention": "Forecast Needs Attention",
                "Good": "Good Forecast Health",
                "Excellent": "Excellent Forecast Health",
            }
        ).fillna("Unknown Forecast Health")
        factor_text = risk_factor + "; " + health_factor
        factor_text = factor_text.mask(
            df["_Manager_Review"], factor_text + "; Manager Review"
        )
        unknown_evidence = risk_factor.eq("Unknown Risk") | health_factor.eq(
            "Unknown Forecast Health"
        )
        factor_text = factor_text.mask(
            unknown_evidence, factor_text + "; Data Quality Issue"
        )
        factors = factor_text.str.split("; ")
        upstream_factors = df["Risk_Factors"].map(
            lambda values: values if isinstance(values, list) else []
        )
        df["Decision_Factors"] = factors + upstream_factors
        return df

    def _assign_priority(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign priority using risk, health, and manager-review rules."""

        risk_priority = df["Risk_Level"].map(RISK_PRIORITY_RULES).fillna(MEDIUM)
        health_priority = df["Forecast_Health"].map(
            HEALTH_PRIORITY_RULES
        ).fillna(MEDIUM)
        risk_rank = risk_priority.map(PRIORITY_RANK).fillna(0).astype(int)
        health_rank = health_priority.map(PRIORITY_RANK).fillna(0).astype(int)
        priority_rank = pd.concat(
            [risk_rank, health_rank], axis=1
        ).max(axis=1)
        priority_rank = priority_rank.mask(
            df["_Manager_Review"], PRIORITY_RANK[CRITICAL]
        )
        df["Recommendation_Priority"] = priority_rank.map(RANK_PRIORITY)
        return df

    def _assign_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign categories through an ordered evidence rule table."""

        factor_text = df["Decision_Factors"].str.join("|")
        category = pd.Series("Forecast Review", index=df.index, dtype="string")
        matched = pd.Series(False, index=df.index)
        for factor, result in CATEGORY_RULES:
            applies = factor_text.str.contains(factor, regex=False) & ~matched
            category = category.mask(applies, result)
            matched |= applies
        df["Recommendation_Category"] = category
        return df

    def _generate_recommendation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select an approved action through ordered mapping rules."""

        factor_text = df["Decision_Factors"].str.join("|")
        action = df["Recommendation_Category"].map(CATEGORY_ACTION_RULES)
        matched = pd.Series(False, index=df.index)
        for factor, result in ACTION_FACTOR_RULES:
            applies = factor_text.str.contains(factor, regex=False) & ~matched
            action = action.mask(applies, result)
            matched |= applies
        standard_conditions = factor_text.str.contains(
            "Low Risk", regex=False
        ) & factor_text.str.contains(
            "Excellent Forecast Health", regex=False
        )
        action = action.mask(
            standard_conditions, "Continue standard forecast monitoring."
        )
        df["Recommended_Action"] = action.fillna(
            "Review forecast assumptions."
        )
        return df

    def _assign_owner(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign accountable owners using category mappings."""

        df["Recommended_Owner"] = (
            df["Recommendation_Category"]
            .map(OWNER_RULES)
            .fillna("Forecast Governance Team")
        )
        return df

    def _generate_reason(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate evidence-backed reasons and recommendation confidence."""

        factors = df["Decision_Factors"]
        factor_text = factors.str.join("|")
        reason_text = pd.Series("", index=df.index, dtype="string")
        reason_count = pd.Series(0, index=df.index, dtype=int)
        for factor, clause in REASON_RULES.items():
            applies = factor_text.str.contains(factor, regex=False)
            separator = reason_text.ne("").map({True: "; ", False: ""})
            reason_text = reason_text.mask(
                applies & reason_count.lt(3),
                reason_text + separator + clause,
            )
            reason_count += applies.astype(int)
        df["Recommendation_Reason"] = reason_text.mask(
            reason_text.eq(""),
            "Available analytics support standard forecast monitoring",
        ) + "."

        df["Recommendation_Confidence"] = (
            reason_count.clip(0, 5) * 20.0
        )
        return df

    def _generate_summary(self, df: pd.DataFrame) -> RecommendationSummary:
        """Aggregate row-level decisions into a recommendation summary."""

        if df.empty:
            return {
                "critical_recommendations": 0,
                "high_priority_recommendations": 0,
                "medium_priority_recommendations": 0,
                "low_priority_recommendations": 0,
                "manager_reviews_required": 0,
                "top_recommendation_category": "",
                "top_recommended_owner": "",
                "highest_confidence": 0.0,
                "average_confidence": 0.0,
                "top_recommendations": [],
            }

        category_counts = df["Recommendation_Category"].value_counts()
        owner_counts = df["Recommended_Owner"].value_counts()
        
        from models.review_models import RecommendationCard
        priority_map = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        recs_df = df[["Recommendation_Priority", "Recommended_Action", "Recommendation_Reason", "Recommendation_Category"]].drop_duplicates()
        recs_df = recs_df.copy()
        recs_df["_weight"] = recs_df["Recommendation_Priority"].map(priority_map).fillna(5)
        recs_df = recs_df.sort_values("_weight").head(10)
        
        top_recs = []
        for _, row in recs_df.iterrows():
            top_recs.append(
                RecommendationCard(
                    priority=str(row["Recommendation_Priority"]),
                    action=str(row["Recommended_Action"]),
                    reason=str(row["Recommendation_Reason"]),
                    category=str(row["Recommendation_Category"])
                )
            )

        summary: RecommendationSummary = {
            "critical_recommendations": int(
                df["Recommendation_Priority"].eq(CRITICAL).sum()
            ),
            "high_priority_recommendations": int(
                df["Recommendation_Priority"].eq(HIGH).sum()
            ),
            "medium_priority_recommendations": int(
                df["Recommendation_Priority"].eq(MEDIUM).sum()
            ),
            "low_priority_recommendations": int(
                df["Recommendation_Priority"].eq(LOW).sum()
            ),
            "manager_reviews_required": int(df["_Manager_Review"].sum()),
            "top_recommendation_category": str(category_counts.idxmax()),
            "top_recommended_owner": str(owner_counts.idxmax()),
            "highest_confidence": float(
                df["Recommendation_Confidence"].max()
            ),
            "average_confidence": float(
                df["Recommendation_Confidence"].mean()
            ),
            "top_recommendations": top_recs,
        }
        return summary
