from dataclasses import dataclass
from core.foundation.execution_context import ExecutionContext
from .exceptions import ContractValidationException

@dataclass(frozen=True)
class RenderedDocument:
    """
    Represents the final renderer output.
    """
    execution_context: ExecutionContext
    mime_type: str
    document_bytes: bytes
    checksum: str
    renderer_version: str
    page_count: int

    def __post_init__(self):
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.mime_type, str) or not self.mime_type.strip():
            raise ContractValidationException("mime_type must be a non-empty string.")
        if not isinstance(self.document_bytes, bytes):
            raise ContractValidationException("document_bytes must be of type bytes.")
        if not isinstance(self.checksum, str) or not self.checksum.strip():
            raise ContractValidationException("checksum must be a non-empty string.")
        if not isinstance(self.renderer_version, str) or not self.renderer_version.strip():
            raise ContractValidationException("renderer_version must be a non-empty string.")
        if not isinstance(self.page_count, int) or self.page_count < 0:
            raise ContractValidationException("page_count must be a non-negative integer.")
