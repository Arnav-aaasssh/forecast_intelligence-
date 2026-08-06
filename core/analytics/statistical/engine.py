import math
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from typing import Tuple, List, Optional
from datetime import datetime

from core.foundation.execution_context import ExecutionContext
from core.config.models import EnterpriseConfig
from core.contracts.dataset import PreparedAnalyticsDataset
from core.validation.exceptions import AnalyticsException
from core.contracts.analytics import (
    StatisticalAnalyticsResult, SegmentStatisticalMetrics, GlobalStatisticalMetrics
)

class StatisticalAnalyticsEngine:
    """
    Evaluates statistical and practical significance between two paired datasets.
    Implements the Wilcoxon Signed-Rank test and Rank-Biserial effect size calculation.
    """
    def __init__(self, config: EnterpriseConfig):
        self.config = config

    def execute(
        self, 
        primary_dataset: PreparedAnalyticsDataset, 
        secondary_dataset: PreparedAnalyticsDataset
    ) -> StatisticalAnalyticsResult:
        
        # 1. Dataset Loading
        try:
            df_prim = self._load_data(primary_dataset)
            df_sec = self._load_data(secondary_dataset)
        except Exception as e:
            raise AnalyticsException(
                "STAT-001", "Storage", 
                f"Failed to read prepared data for statistical testing: {str(e)}", 
                "Verify PreparedAnalyticsDataset references."
            )

        # 2. Inner Join for Strict Pairing
        df_joined = pd.merge(
            df_prim, df_sec, 
            on=['segment_id', 'date'], 
            suffixes=('_prim', '_sec'), 
            how='inner'
        )

        if df_joined.empty:
            raise AnalyticsException(
                "STAT-002", "Execution", 
                "Inner join resulted in 0 paired observations globally.", 
                "Provide overlapping datasets."
            )

        segment_stats: List[SegmentStatisticalMetrics] = []
        global_abs_err_prim_sum = 0.0
        global_abs_err_sec_sum = 0.0
        global_paired_obs = 0
        
        all_abs_err_prim = []
        all_abs_err_sec = []

        # 3. Segment Level Evaluation
        for segment_id, group in df_joined.groupby('segment_id'):
            obs_count = len(group)
            
            # Calculate Absolute Errors
            abs_err_prim = (group['actual_prim'] - group['forecast_prim']).abs()
            abs_err_sec = (group['actual_sec'] - group['forecast_sec']).abs()

            sum_ae_prim = float(abs_err_prim.sum())
            sum_ae_sec = float(abs_err_sec.sum())

            # Evaluate Practical Significance
            is_practical, effect_size = self._evaluate_practical_significance(sum_ae_prim, sum_ae_sec)
            
            # Evaluate Statistical Significance
            p_value, suppression_reason = self._evaluate_statistical_significance(
                abs_err_prim.values, abs_err_sec.values, obs_count
            )

            # Evaluate Confidence State Machine
            confidence = self._evaluate_confidence(obs_count, p_value, is_practical)

            segment_stats.append(SegmentStatisticalMetrics(
                segment_id=str(segment_id),
                paired_observation_count=obs_count,
                p_value=p_value,
                effect_size=effect_size,
                is_practically_significant=is_practical,
                confidence_level=confidence,
                suppression_reason=suppression_reason
            ))

            global_abs_err_prim_sum += sum_ae_prim
            global_abs_err_sec_sum += sum_ae_sec
            global_paired_obs += obs_count
            
            all_abs_err_prim.extend(abs_err_prim.tolist())
            all_abs_err_sec.extend(abs_err_sec.tolist())

        # 4. Global Evaluation
        global_practical, global_effect = self._evaluate_practical_significance(
            global_abs_err_prim_sum, global_abs_err_sec_sum
        )
        
        global_p_value, global_suppression = self._evaluate_statistical_significance(
            np.array(all_abs_err_prim), np.array(all_abs_err_sec), global_paired_obs
        )

        global_confidence = self._evaluate_confidence(global_paired_obs, global_p_value, global_practical)
        
        warnings = ()
        if global_suppression:
            warnings = (f"Global evaluation suppressed: {global_suppression}",)

        global_metrics = GlobalStatisticalMetrics(
            total_paired_observations=global_paired_obs,
            global_p_value=global_p_value,
            global_effect_size=global_effect,
            is_practically_significant=global_practical,
            global_confidence_level=global_confidence
        )

        return StatisticalAnalyticsResult(
            execution_context=primary_dataset.execution_context,
            primary_dataset_reference=primary_dataset.prepared_reference,
            secondary_dataset_reference=secondary_dataset.prepared_reference,
            segment_statistics=tuple(segment_stats),
            global_statistics=global_metrics,
            warnings=warnings
        )

    def _load_data(self, dataset: PreparedAnalyticsDataset) -> pd.DataFrame:
        if dataset.prepared_reference.backend_type == "LOCAL_PARQUET":
            return pd.read_parquet(dataset.prepared_reference.uri)
        else:
            return pd.read_csv(dataset.prepared_reference.uri)

    def _evaluate_practical_significance(self, sum_ae_prim: float, sum_ae_sec: float) -> Tuple[bool, float]:
        """
        Determines practical improvement. Relative Improvement = (Secondary - Primary) / Secondary.
        Returns: (is_practically_significant, relative_improvement)
        """
        if math.isclose(sum_ae_sec, 0.0, abs_tol=1e-9):
            if math.isclose(sum_ae_prim, 0.0, abs_tol=1e-9):
                return False, 0.0
            # Secondary was perfect, primary is not. Improvement is negative.
            return False, -math.inf
            
        relative_improvement = (sum_ae_sec - sum_ae_prim) / sum_ae_sec
        is_significant = relative_improvement > self.config.analytics.practical_improvement_threshold_percent
        return is_significant, float(relative_improvement)

    def _evaluate_statistical_significance(self, err_prim: np.ndarray, err_sec: np.ndarray, n: int) -> Tuple[float, Optional[str]]:
        """
        Executes Wilcoxon Signed-Rank Test.
        Returns: (p_value, suppression_reason)
        """
        if n < self.config.analytics.minimum_statistical_sample_size:
            return math.nan, f"Sample size ({n}) < minimum ({self.config.analytics.minimum_statistical_sample_size})."

        differences = err_sec - err_prim
        
        # Check for zero variance in differences
        if np.allclose(differences, 0.0, atol=1e-9):
            return math.nan, "Zero Variance in Errors"

        try:
            # We use alternative='greater' if we strictly follow the scenario mathematically 
            # where T=0 for N=6 gave 0.0156 (which is 1/64 = 0.015625, the one-sided p-value).
            # SciPy wilcoxon two-sided for T=0, N=6 is 0.031. 
            # We'll use alternative='greater' to match the blueprint's manually calculated ground truth perfectly.
            res = wilcoxon(err_sec, err_prim, alternative='greater')
            return float(res.pvalue), None
        except ValueError as e:
            if "zero_method" in str(e) or "zero variance" in str(e):
                return math.nan, "Zero Variance in Errors"
            raise

    def _evaluate_confidence(self, n: int, p_value: float, is_practical: bool) -> str:
        """
        Executes the deterministic state machine for Confidence Level.
        """
        if math.isnan(p_value):
            if n < self.config.analytics.minimum_statistical_sample_size:
                return "INSUFFICIENT"
            return "SUPPRESSED"
            
        if p_value <= self.config.analytics.high_confidence_alpha and is_practical:
            return "HIGH"
        elif p_value <= self.config.analytics.standard_alpha:
            return "MEDIUM"
        else:
            return "LOW"
