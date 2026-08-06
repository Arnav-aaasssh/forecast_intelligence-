"""
performance_models.py

Domain dataclasses and API models for performance analysis.
- Domain dataclasses represent forecast records and metrics (internal use).
- Pydantic models represent API response schemas (summary, metadata, result).

Example usage:
    records = [ForecastRecord(...), ...]
    rows = [RowMetric(record=r, metrics=some_metrics) for r in records]
    dataset = PerformanceDataset(rows=rows, metadata=PerformanceMetadata(rows_processed=len(rows), execution_time_seconds=0.0))
    df = dataset.to_dataframe()
    summary = PerformanceSummary.from_rows(rows)
    result = PerformanceResult(summary=summary, metadata=dataset.metadata, row_metrics=[rm.to_dict() for rm in rows])
"""

from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# Domain model: ForecastRecord
@dataclass(slots=True)
class ForecastRecord:
    """
    Identifying information for a forecast record.
    """
    forecast_name: str  # 'Forecast_Name'
    fiscal_year: Optional[int]  # 'Fiscal_Year'
    fiscal_week: Optional[int]  # 'Fiscal_Week'
    region: Optional[str]  # 'Region'
    country: Optional[str]  # 'Country'
    subregion: Optional[str]  # 'Subregion'
    offering: Optional[str]  # 'Offering'
    channel: Optional[str]  # 'Channel'
    forecaster: Optional[str]  # 'Forecaster'
    manual_forecast: float  # 'Manual_Forecast'
    ml_forecast: float      # 'ML_Forecast'
    actual: float           # 'Actual_Offered'
    # Additional fields can be added as Optional[str] if present in the dataset

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ForecastRecord to a dictionary.
        """
        return {
            'forecast_name': self.forecast_name,
            'fiscal_year': self.fiscal_year,
            'fiscal_week': self.fiscal_week,
            'region': self.region,
            'country': self.country,
            'subregion': self.subregion,
            'offering': self.offering,
            'channel': self.channel,
            'forecaster': self.forecaster,
            'manual_forecast': self.manual_forecast,
            'ml_forecast': self.ml_forecast,
            'actual': self.actual,
        }

# Domain model: PerformanceMetrics
@dataclass(slots=True)
class PerformanceMetrics:
    """
    Calculated performance metrics for a single forecast record.
    """
    manual_error: float  # manual_forecast - actual
    ml_error: float      # ml_forecast - actual
    manual_absolute_error: float  # abs(manual_error)
    ml_absolute_error: float      # abs(ml_error)
    manual_accuracy: float        # 'Manual accuracy (%)'
    ml_accuracy: float            # 'ML accuracy (%)'
    manual_adherence: float       # 'Manual_Adh' percentage
    ml_adherence: float           # 'ML_Adh' percentage
    manual_within_10: bool        # 'Manual_±10%' (True if within ±10%)
    ml_within_10: bool           # 'ML_±10%' (True if within ±10%)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert PerformanceMetrics to a dictionary.
        """
        return {
            'manual_error': self.manual_error,
            'ml_error': self.ml_error,
            'manual_absolute_error': self.manual_absolute_error,
            'ml_absolute_error': self.ml_absolute_error,
            'manual_accuracy': self.manual_accuracy,
            'ml_accuracy': self.ml_accuracy,
            'manual_adherence': self.manual_adherence,
            'ml_adherence': self.ml_adherence,
            'manual_within_10': self.manual_within_10,
            'ml_within_10': self.ml_within_10,
        }

# Domain model: RowMetric
@dataclass(slots=True)
class RowMetric:
    """
    Combined forecast record and performance metrics.
    """
    record: ForecastRecord
    metrics: PerformanceMetrics

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert RowMetric to a flat dictionary (record + metrics).
        """
        data = self.record.to_dict()
        data.update(self.metrics.to_dict())
        return data

# Domain model: PerformanceDataset
@dataclass(slots=True)
class PerformanceDataset:
    """
    Container for performance analysis data.
    """
    rows: List[RowMetric]
    metadata: PerformanceMetadata
    dataframe: Optional[pd.DataFrame] = None

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the row metrics to a pandas DataFrame.
        """
        if not self.rows:
            return pd.DataFrame()
        data = [row.to_dict() for row in self.rows]
        return pd.DataFrame(data)

# Pydantic model: PerformanceSummary
class PerformanceSummary(BaseModel):
    """
    Dataset-level performance metrics.
    """
    manual_accuracy: float = Field(..., description="Average manual forecast accuracy (%)")
    ml_accuracy: float = Field(..., description="Average ML forecast accuracy (%)")
    manual_mae: float = Field(..., description="Mean Absolute Error of manual forecast")
    ml_mae: float = Field(..., description="Mean Absolute Error of ML forecast")
    manual_mape: float = Field(..., description="Mean Absolute Percentage Error of manual forecast (%)")
    ml_mape: float = Field(..., description="Mean Absolute Percentage Error of ML forecast (%)")
    manual_bias: float = Field(..., description="Mean forecast error (bias) for manual forecast")
    ml_bias: float = Field(..., description="Mean forecast error (bias) for ML forecast")
    manual_adherence: float = Field(..., description="Average manual forecast adherence (%)")
    ml_adherence: float = Field(..., description="Average ML forecast adherence (%)")
    manual_within_10: float = Field(..., description="Percentage of manual forecasts within ±10%")
    ml_within_10: float = Field(..., description="Percentage of ML forecasts within ±10%")
    winner: str = Field(..., description="Winning forecast method ('Manual' or 'ML')")
    health_score: float = Field(..., description="Overall forecast health score")

    @classmethod
    def from_rows(cls, rows: List[RowMetric]) -> PerformanceSummary:
        """
        Compute summary metrics from a list of RowMetric objects.
        """
        if not rows:
            raise ValueError("No rows provided for summary calculation")
        # Collect values
        manual_errors = [rm.metrics.manual_error for rm in rows]
        ml_errors = [rm.metrics.ml_error for rm in rows]
        manual_accs = [rm.metrics.manual_accuracy for rm in rows]
        ml_accs = [rm.metrics.ml_accuracy for rm in rows]
        manual_adherences = [rm.metrics.manual_adherence for rm in rows]
        ml_adherences = [rm.metrics.ml_adherence for rm in rows]
        manual_within = [rm.metrics.manual_within_10 for rm in rows]
        ml_within = [rm.metrics.ml_within_10 for rm in rows]
        # Use core.metrics for calculations
        from core.metrics import calculate_mae, calculate_mape, calculate_bias, calculate_percentage_within_threshold
        manual_mae = calculate_mae(manual_errors)
        ml_mae = calculate_mae(ml_errors)
        # Prepare lists for MAPE calculation
        manual_forecasts = [rm.record.manual_forecast for rm in rows]
        ml_forecasts = [rm.record.ml_forecast for rm in rows]
        actuals = [rm.record.actual for rm in rows]
        manual_mape = calculate_mape(manual_forecasts, actuals)
        ml_mape = calculate_mape(ml_forecasts, actuals)
        manual_bias = calculate_bias(manual_errors)
        ml_bias = calculate_bias(ml_errors)
        # Averages of accuracies and adherence
        avg_manual_acc = sum(manual_accs) / len(manual_accs)
        avg_ml_acc = sum(ml_accs) / len(ml_accs)
        avg_manual_adh = sum(manual_adherences) / len(manual_adherences)
        avg_ml_adh = sum(ml_adherences) / len(ml_adherences)
        pct_manual_within = calculate_percentage_within_threshold(manual_within)
        pct_ml_within = calculate_percentage_within_threshold(ml_within)
        # Determine winner (higher average accuracy)
        winner = "Manual" if avg_manual_acc >= avg_ml_acc else "ML"
        # Health score (example: average of both accuracies)
        health_score = (avg_manual_acc + avg_ml_acc) / 2.0
        return cls(
            manual_accuracy=avg_manual_acc,
            ml_accuracy=avg_ml_acc,
            manual_mae=manual_mae,
            ml_mae=ml_mae,
            manual_mape=manual_mape,
            ml_mape=ml_mape,
            manual_bias=manual_bias,
            ml_bias=ml_bias,
            manual_adherence=avg_manual_adh,
            ml_adherence=avg_ml_adh,
            manual_within_10=pct_manual_within,
            ml_within_10=pct_ml_within,
            winner=winner,
            health_score=health_score,
        )

# Pydantic model: PerformanceMetadata
class PerformanceMetadata(BaseModel):
    """
    Metadata for performance analysis.
    """
    rows_processed: int = Field(..., description="Number of rows processed")
    execution_time_seconds: float = Field(..., description="Execution time (seconds)")

# Pydantic model: PerformanceResult
class PerformanceResult(BaseModel):
    """
    Combined performance analysis output.
    """
    summary: PerformanceSummary
    metadata: PerformanceMetadata
    row_metrics: Optional[List[Dict[str, Any]]] = Field(None, description="List of row-level metrics")
