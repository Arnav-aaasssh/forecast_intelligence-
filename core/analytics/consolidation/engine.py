from datetime import datetime, timezone
import uuid
from typing import Optional

from core.contracts.analytics import ForecastAccuracyResult, StatisticalAnalyticsResult, ModelEvidence, AnalyticalEvidenceBundle
from core.validation.exceptions import AnalyticsException
from core.config.models import EnterpriseConfig

class EvidenceIntegrityValidator:
    """
    Verifies the referential and temporal integrity of disparate analytical evidence 
    before consolidation.
    """
    @staticmethod
    def validate(primary_accuracy: ForecastAccuracyResult, 
                 secondary_accuracy: Optional[ForecastAccuracyResult], 
                 statistical_result: Optional[StatisticalAnalyticsResult]):
        prim_ctx = primary_accuracy.execution_context
        
        if secondary_accuracy:
            sec_ctx = secondary_accuracy.execution_context
            if prim_ctx.run_id != sec_ctx.run_id:
                raise AnalyticsException("EVAL-001", "CONSOLIDATION_ERROR", 
                                         "ExecutionContext run_id mismatch between primary and secondary accuracy.", 
                                         "Ensure both models are evaluated in the same run.", 
                                         execution_context_id=str(prim_ctx.run_id))
            if primary_accuracy.evaluation_window != secondary_accuracy.evaluation_window:
                raise AnalyticsException("EVAL-002", "CONSOLIDATION_ERROR", 
                                         "Temporal window mismatch between models.", 
                                         "Align evaluation windows.")
                
        if statistical_result:
            stat_ctx = statistical_result.execution_context
            if prim_ctx.run_id != stat_ctx.run_id:
                raise AnalyticsException("EVAL-003", "CONSOLIDATION_ERROR", 
                                         "ExecutionContext run_id mismatch between accuracy and statistics.", 
                                         "Ensure statistical analytics are run in the same context.", 
                                         execution_context_id=str(prim_ctx.run_id))
            
            if statistical_result.primary_dataset_reference != primary_accuracy.prepared_dataset_reference:
                raise AnalyticsException("EVAL-004", "CONSOLIDATION_ERROR", 
                                         "Primary dataset mismatch between accuracy and statistical results.", 
                                         "Use the same primary dataset.")
                
            if secondary_accuracy and statistical_result.secondary_dataset_reference != secondary_accuracy.prepared_dataset_reference:
                 raise AnalyticsException("EVAL-005", "CONSOLIDATION_ERROR", 
                                          "Secondary dataset mismatch between accuracy and statistical results.", 
                                          "Use the same secondary dataset.")

class AnalyticalEvidenceConsolidationEngine:
    """
    Final Engine in the Analytics Layer.
    Consolidates disparate mathematical evidence (Forecast Accuracy, Statistical Analytics) 
    into a single immutable AnalyticalEvidenceBundle. 
    Applies no business logic, ranking, or operational policies.
    """
    def __init__(self, config: EnterpriseConfig):
        self.config = config
        self.validator = EvidenceIntegrityValidator()
        
    def execute(self, 
                primary_id: str,
                primary_accuracy: ForecastAccuracyResult, 
                secondary_id: Optional[str] = None,
                secondary_accuracy: Optional[ForecastAccuracyResult] = None,
                statistical_result: Optional[StatisticalAnalyticsResult] = None) -> AnalyticalEvidenceBundle:
        
        if not primary_id or not primary_accuracy:
            raise AnalyticsException("EVAL-006", "CONSOLIDATION_ERROR", 
                                     "Missing primary model or accuracy result.", 
                                     "Provide primary model evidence.")
            
        if bool(secondary_id) != bool(secondary_accuracy):
            raise AnalyticsException("EVAL-007", "CONSOLIDATION_ERROR", 
                                     "Secondary model ID and accuracy result must both be provided or both omitted.", 
                                     "Provide both or neither.")
            
        self.validator.validate(primary_accuracy, secondary_accuracy, statistical_result)
        
        primary_evidence = ModelEvidence(
            model_identifier=primary_id,
            is_primary=True,
            accuracy_metrics=primary_accuracy,
            statistical_metrics=statistical_result
        )
        
        secondary_evidence = None
        if secondary_id and secondary_accuracy:
            secondary_evidence = ModelEvidence(
                model_identifier=secondary_id,
                is_primary=False,
                accuracy_metrics=secondary_accuracy,
                statistical_metrics=None 
            )
            
        return AnalyticalEvidenceBundle(
            primary_evidence=primary_evidence,
            secondary_evidence=secondary_evidence,
            execution_context=primary_accuracy.execution_context,
            traceability_id=uuid.uuid4(),
            consolidation_timestamp=datetime.now(timezone.utc)
        )
