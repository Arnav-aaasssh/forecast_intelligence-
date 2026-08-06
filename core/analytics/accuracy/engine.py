import math
from datetime import datetime
import pandas as pd
from typing import Tuple, List
import uuid

from core.foundation.execution_context import ExecutionContext
from core.config.models import EnterpriseConfig
from core.contracts.dataset import PreparedAnalyticsDataset, PreparedSegmentMetadata
from core.validation.exceptions import AnalyticsException
from core.contracts.analytics import (
    ForecastAccuracyResult, GlobalAccuracyMetrics, 
    SegmentAccuracyMetrics, MetricMetadata
)

class ForecastAccuracyEngine:
    def __init__(self, config: EnterpriseConfig):
        self.config = config

    def execute(self, prepared_dataset: PreparedAnalyticsDataset) -> ForecastAccuracyResult:
        if prepared_dataset.total_eligible_segments == 0:
            raise AnalyticsException("ACC-001", "Execution", "Insufficient Data for Accuracy Calculation. 0 eligible segments.", "Provide a dataset with qualifying segments.")
            
        try:
            if prepared_dataset.prepared_reference.backend_type == "LOCAL_PARQUET":
                df = pd.read_parquet(prepared_dataset.prepared_reference.uri)
            else:
                df = pd.read_csv(prepared_dataset.prepared_reference.uri)
        except Exception as e:
            raise AnalyticsException("ACC-002", "Storage", f"Failed to read prepared data: {str(e)}", "Verify PreparedAnalyticsDataset reference.")
            
        # Drop Nulls
        df = df.dropna(subset=['actual', 'forecast'])
        
        # Enforce Non-Negative Actuals
        if (df['actual'] < 0).any():
            raise AnalyticsException("ACC-003", "Data Quality", "Negative actuals detected. Actuals must be >= 0.", "Cleanse negative actuals upstream.")

        segment_metrics: List[SegmentAccuracyMetrics] = []
        
        # We need these to accumulate for the global metrics
        global_sum_absolute_error = 0.0
        global_sum_error = 0.0
        global_sum_actual = 0.0
        
        global_sum_weighted_mae = 0.0
        global_sum_weighted_rmse = 0.0
        global_sum_weighted_hit_rate = 0.0
        
        total_observations = 0
        
        eligible_segment_ids = {s.segment_id for s in prepared_dataset.segment_metadata if s.is_eligible}
        
        tolerance = self.config.analytics.acceptable_tolerance_percentage
        
        # Compute Segment Metrics
        for segment_id, group in df.groupby('segment_id'):
            if segment_id not in eligible_segment_ids:
                continue
                
            obs_count = len(group)
            if obs_count == 0:
                continue
                
            actual_sum = float(group['actual'].sum())
            forecast_sum = float(group['forecast'].sum())
            
            absolute_errors = (group['actual'] - group['forecast']).abs()
            errors = group['forecast'] - group['actual']
            
            sum_absolute_error = float(absolute_errors.sum())
            sum_error = float(errors.sum())
            
            # MAE & RMSE
            mae = float(absolute_errors.mean())
            rmse = float(math.sqrt((errors ** 2).mean()))
            
            # Hit Rate
            # tolerance * actual. (If actual is 0, then hit if forecast == 0)
            hits = (absolute_errors <= (tolerance * group['actual'])).sum()
            hit_rate = float(hits / obs_count)
            
            wape = self._calculate_ratio(sum_absolute_error, actual_sum)
            bias = self._calculate_ratio(sum_error, actual_sum)
            
            segment_metrics.append(SegmentAccuracyMetrics(
                segment_id=str(segment_id),
                observation_count=obs_count,
                wape=wape,
                bias=bias,
                mae=mae,
                rmse=rmse,
                hit_rate=hit_rate
            ))
            
            global_sum_absolute_error += sum_absolute_error
            global_sum_error += sum_error
            global_sum_actual += actual_sum
            
            global_sum_weighted_mae += (mae * actual_sum)
            global_sum_weighted_rmse += (rmse * actual_sum)
            global_sum_weighted_hit_rate += (hit_rate * actual_sum)
            
            total_observations += obs_count

        if not segment_metrics:
            raise AnalyticsException("ACC-004", "Execution", "No eligible segments survived null-filtering.", "Adjust minimum sample size or fix null data.")
            
        global_wape = self._calculate_ratio(global_sum_absolute_error, global_sum_actual)
        global_bias = self._calculate_ratio(global_sum_error, global_sum_actual)
        
        # Weighted averages for MAE, RMSE, HitRate
        vol_weighted_mae = self._calculate_ratio(global_sum_weighted_mae, global_sum_actual)
        vol_weighted_rmse = self._calculate_ratio(global_sum_weighted_rmse, global_sum_actual)
        vol_weighted_hit_rate = self._calculate_ratio(global_sum_weighted_hit_rate, global_sum_actual)

        metric_metadata = MetricMetadata(
            engine_version="1.0.0",
            calculation_timestamp=datetime.utcnow(),
            zero_actuals_policy_applied=self.config.analytics.zero_actuals_policy,
            acceptable_tolerance_applied=tolerance
        )
        
        global_metrics = GlobalAccuracyMetrics(
            total_observation_count=total_observations,
            global_wape=global_wape,
            global_bias=global_bias,
            volume_weighted_mae=vol_weighted_mae,
            volume_weighted_rmse=vol_weighted_rmse,
            volume_weighted_hit_rate=vol_weighted_hit_rate
        )

        return ForecastAccuracyResult(
            execution_context=prepared_dataset.execution_context,
            prepared_dataset_reference=prepared_dataset.prepared_reference,
            evaluation_window=prepared_dataset.window_metadata,
            metric_metadata=metric_metadata,
            segment_metrics=tuple(segment_metrics),
            global_metrics=global_metrics
        )

    def _calculate_ratio(self, numerator: float, denominator: float) -> float:
        if math.isclose(denominator, 0.0, abs_tol=1e-9):
            policy = self.config.analytics.zero_actuals_policy
            
            if math.isclose(numerator, 0.0, abs_tol=1e-9):
                # 0/0 is a perfect score (actual=0, forecast=0) -> error is 0.0
                # Wait, if WAPE is error/actual and both are 0, WAPE = 0.0. 
                # Same for Bias. For MAE weight, if weight=0, we shouldn't really reach here unless ALL segments are 0 volume.
                return 0.0
                
            if policy == "RETURN_INFINITY":
                # For bias, numerator could be negative. Infinity sign matters.
                return math.inf if numerator > 0 else -math.inf
            elif policy == "RETURN_NAN":
                return math.nan
            elif policy == "RETURN_ZERO":
                return 0.0
            elif policy == "RAISE_EXCEPTION":
                raise AnalyticsException("ACC-005", "Math", "Zero actuals denominator encountered with RAISE_EXCEPTION policy.", "Change policy or adjust data.")
            else: # SUPPRESS_METRIC mapped to nan in raw math, serialization drops it
                return math.nan
                
        return float(numerator / denominator)
