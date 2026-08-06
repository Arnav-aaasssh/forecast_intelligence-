"""
Defines immutable metric objects for tracking LLM provider health.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ProviderMetrics:
    """
    Immutable structured metrics object for tracking LLM provider health and observability.
    """
    execution_id: str
    provider_name: str
    model_name: str
    request_duration_ms: float
    retry_count: int
    response_size_bytes: int
    success: bool
    provider_outcome: str  # "SUCCESS", "TIMEOUT", "HTTP_ERROR", "PARSING_ERROR"
    circuit_state: str     # "CLOSED", "OPEN", "HALF_OPEN"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Newly expanded fields
    token_usage: Optional[int] = None
    retry_delays: Optional[list[float]] = None
    http_status: Optional[int] = None
    failure_category: Optional[str] = None
    cache_status: str = "MISS"  # "HIT", "MISS", "BYPASS"
    error_type: Optional[str] = None

    def as_dict(self) -> dict:
        return self.__dict__
