import uuid
from typing import Tuple
from core.contracts.analytics import AnalyticalEvidenceBundle
from core.contracts.decision import DecisionContract
from core.contracts.content import BusinessQuestionContract, StructuredSection
from core.content.engine.generators import (
    EvidenceGenerator, 
    ObservationGenerator, 
    ConclusionGenerator, 
    DecisionProjectionGenerator
)
from core.validation.exceptions import AnalyticsException

class SectionValidator:
    def validate(self, section: StructuredSection):
        if not isinstance(section, StructuredSection):
            raise AnalyticsException("CON-002", "CONTENT_ERROR", "Output must be StructuredSection", "Check assembler.")

class SectionAssembler:
    def assemble(self, bq_id: str, observation: str, conclusion: str, decision_support: str,
                 primary: tuple, supporting: tuple, recommendation: str, is_suppressed: bool,
                 decision: DecisionContract) -> StructuredSection:
                 
        return StructuredSection(
            business_question_id=bq_id,
            observation=observation,
            conclusion=conclusion,
            decision_support=decision_support,
            primary_evidence=primary,
            supporting_evidence=supporting,
            recommendation=recommendation,
            recommendation_suppressed=is_suppressed,
            charts_referenced=(),
            execution_context_id=str(decision.execution_context.run_id),
            traceability_id=str(decision.traceability_id),
            version="1.0"
        )

class ContentOrchestrator:
    def __init__(self):
        self.evidence_gen = EvidenceGenerator()
        self.obs_gen = ObservationGenerator()
        self.conc_gen = ConclusionGenerator()
        self.decision_proj = DecisionProjectionGenerator()
        self.assembler = SectionAssembler()
        self.validator = SectionValidator()
        
    def execute(self, bq_contract: BusinessQuestionContract, decision: DecisionContract, bundle: AnalyticalEvidenceBundle, is_suppressed: bool = False) -> StructuredSection:
        if not isinstance(bq_contract, BusinessQuestionContract):
            raise AnalyticsException("CON-003", "CONTENT_ERROR", "Invalid BusinessQuestionContract", "Provide valid contract.")
        if not isinstance(decision, DecisionContract):
            raise AnalyticsException("CON-004", "CONTENT_ERROR", "Invalid DecisionContract", "Provide valid decision.")
        if not isinstance(bundle, AnalyticalEvidenceBundle):
            raise AnalyticsException("CON-005", "CONTENT_ERROR", "Invalid AnalyticalEvidenceBundle", "Provide valid bundle.")
            
        primary, supporting = self.evidence_gen.generate(bundle, bq_contract)
        
        observation = self.obs_gen.generate(bq_contract, primary, supporting)
        conclusion, decision_support = self.conc_gen.generate(bq_contract, primary, supporting)
        recommendation, suppressed_flag = self.decision_proj.generate(decision, is_suppressed)
        
        section = self.assembler.assemble(
            bq_contract.business_question_id,
            observation,
            conclusion,
            decision_support,
            primary,
            supporting,
            recommendation,
            suppressed_flag,
            decision
        )
        
        self.validator.validate(section)
        return section
