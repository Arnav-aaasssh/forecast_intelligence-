"""
Canonical data contracts for the LLM subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutiveSummary:
    content: str
    generated_at: str
    provider: str
    model: str


@dataclass(frozen=True, slots=True)
class ManagerSummary:
    content: str
    generated_at: str
    provider: str
    model: str


@dataclass(frozen=True, slots=True)
class EmailSummary:
    content: str
    generated_at: str
    provider: str
    model: str


@dataclass(frozen=True, slots=True)
class TeamsSummary:
    content: str
    generated_at: str
    provider: str
    model: str


@dataclass(frozen=True, slots=True)
class SummaryBundle:
    """Aggregate bundle representing the complete LLM pipeline output."""
    executive: ExecutiveSummary
    manager: ManagerSummary
    email: EmailSummary
    teams: TeamsSummary


class SummaryBundleFactory:
    """Factory for creating SummaryBundle instances, including fallbacks."""

    @staticmethod
    def create_placeholder_bundle(reason: str) -> SummaryBundle:
        """
        Creates a deterministic fallback bundle when the LLM provider fails.
        Ensures downstream consumers always receive a complete artifact set.
        """
        placeholder_text = (
            f"**Reason:** {reason}\n\n"
            "Deterministic analytics completed successfully.\n\n"
            "Forecast review results remain valid.\n\n"
            "This summary could not be generated because the external LLM provider was temporarily unavailable."
        )

        now_str = "N/A"
        fallback_provider = "System Fallback"
        fallback_model = "Deterministic Rules"

        return SummaryBundle(
            executive=ExecutiveSummary(content=placeholder_text, generated_at=now_str, provider=fallback_provider, model=fallback_model),
            manager=ManagerSummary(content=placeholder_text, generated_at=now_str, provider=fallback_provider, model=fallback_model),
            email=EmailSummary(content=placeholder_text, generated_at=now_str, provider=fallback_provider, model=fallback_model),
            teams=TeamsSummary(content=placeholder_text, generated_at=now_str, provider=fallback_provider, model=fallback_model)
        )
