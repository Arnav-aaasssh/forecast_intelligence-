"""
Dependency injection module for FastAPI.

Bridges the FastAPI dependency system with the application's ServiceRegistry.
"""

from typing import Callable

from services.service_registry import create_forecast_review_service

# To ensure the service is instantiated only when needed (or cached appropriately)
# we can instantiate it per request, or cache it if it's completely stateless.
# The user specified: "Every execution should receive a fresh ReviewEngine() since your engine is intentionally stateless."
# The create_forecast_review_service() already gives us a fresh one.

def get_forecast_review_service():
    """FastAPI dependency that returns a fully configured ForecastReviewService."""
    return create_forecast_review_service()
