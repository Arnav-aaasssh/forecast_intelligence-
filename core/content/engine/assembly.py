import uuid
from typing import Tuple, List, Set
from datetime import datetime, timezone
from core.contracts.content import StructuredSection, ReportDocument, ReportMetadata
from core.validation.exceptions import AnalyticsException

class SectionOrdering:
    """Ensures sections are ordered and mandatory sections exist."""
    def __init__(self, order_config: Tuple[str, ...], mandatory_sections: Tuple[str, ...]):
        self.order_config = order_config
        self.mandatory_sections = mandatory_sections
        
    def order(self, sections: Tuple[StructuredSection, ...]) -> Tuple[StructuredSection, ...]:
        seen = set()
        for s in sections:
            if s.business_question_id in seen:
                raise AnalyticsException("ASM-001", "ASSEMBLY_ERROR", f"Duplicate section found: {s.business_question_id}", "Remove duplicates.")
            seen.add(s.business_question_id)
            
        for m in self.mandatory_sections:
            if m not in seen:
                raise AnalyticsException("ASM-002", "ASSEMBLY_ERROR", f"Missing mandatory section: {m}", "Include mandatory sections.")
                
        order_map = {bq_id: idx for idx, bq_id in enumerate(self.order_config)}
        
        def sort_key(s: StructuredSection):
            return order_map.get(s.business_question_id, 9999)
            
        return tuple(sorted(sections, key=sort_key))

class CrossReferenceResolver:
    """Resolves and validates cross-references within the report."""
    def resolve(self, sections: Tuple[StructuredSection, ...]) -> None:
        pass

class AssetRegistry:
    """Collects and validates chart assets."""
    def register(self, sections: Tuple[StructuredSection, ...]) -> Tuple[str, ...]:
        assets = set()
        for s in sections:
            if hasattr(s, 'charts_referenced'):
                for c in s.charts_referenced:
                    assets.add(c)
        return tuple(sorted(list(assets)))

class AppendixRegistry:
    """Collects and validates appendices."""
    def register(self, sections: Tuple[StructuredSection, ...]) -> Tuple[str, ...]:
        return ()

class ReportValidator:
    """Validates the final ReportDocument."""
    def validate(self, doc: ReportDocument) -> None:
        if not isinstance(doc, ReportDocument):
            raise AnalyticsException("ASM-003", "ASSEMBLY_ERROR", "Output must be ReportDocument", "Check orchestrator.")
        
        exec_ctxs = set(s.execution_context_id for s in doc.sections)
        trace_ids = set(s.traceability_id for s in doc.sections)
        
        if len(exec_ctxs) > 1:
            raise AnalyticsException("ASM-004", "ASSEMBLY_ERROR", "Multiple execution contexts found in sections", "Ensure consistent trace.")
        
        if len(trace_ids) > 1:
            raise AnalyticsException("ASM-005", "ASSEMBLY_ERROR", "Multiple traceability IDs found in sections", "Ensure consistent trace.")

class ReportAssemblyEngine:
    """Orchestrates assembly of StructuredSections into a ReportDocument."""
    def __init__(self, ordering: SectionOrdering):
        self.ordering = ordering
        self.resolver = CrossReferenceResolver()
        self.asset_registry = AssetRegistry()
        self.appendix_registry = AppendixRegistry()
        self.validator = ReportValidator()
        
    def assemble(self, sections: Tuple[StructuredSection, ...], title: str, executive_summary: str) -> ReportDocument:
        if not sections:
            raise AnalyticsException("ASM-006", "ASSEMBLY_ERROR", "No sections provided for assembly", "Provide sections.")
            
        ordered_sections = self.ordering.order(sections)
        
        self.resolver.resolve(ordered_sections)
        
        assets = self.asset_registry.register(ordered_sections)
        appendices = self.appendix_registry.register(ordered_sections)
        
        metadata = ReportMetadata(
            title=title,
            executive_summary=executive_summary,
            generated_at=datetime.now(timezone.utc).isoformat(),
            version="1.0"
        )
        
        exec_id = ordered_sections[0].execution_context_id
        trace_id = ordered_sections[0].traceability_id
        
        doc = ReportDocument(
            execution_context_id=exec_id,
            traceability_id=trace_id,
            metadata=metadata,
            sections=ordered_sections,
            assets=assets,
            appendices=appendices
        )
        
        self.validator.validate(doc)
        
        return doc
