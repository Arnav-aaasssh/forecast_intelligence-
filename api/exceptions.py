"""
Exception handlers for the FastAPI presentation layer.

Maps domain exceptions to standardized HTTP responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

from services.exceptions import (
    ConfigurationError,
    DatasetLoadError,
    ReportGenerationError,
    ValidationRuntimeError,
    LLMProviderError,
)

logger = logging.getLogger(__name__)


async def configuration_error_handler(request: Request, exc: ConfigurationError):
    logger.error("ConfigurationError occurred: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Configuration Error", "message": str(exc)},
    )


async def dataset_load_error_handler(request: Request, exc: DatasetLoadError):
    logger.warning("DatasetLoadError occurred: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid Dataset", "message": str(exc)},
    )


async def validation_runtime_error_handler(request: Request, exc: ValidationRuntimeError):
    logger.warning("ValidationRuntimeError occurred: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation Error", "message": str(exc)},
    )


async def llm_provider_error_handler(request: Request, exc: LLMProviderError):
    logger.error("LLMProviderError occurred: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": "LLM Provider Error", "message": str(exc)},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unexpected unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred during processing."},
    )


def register_exception_handlers(app):
    """Register all domain exception handlers with the FastAPI app."""
    app.add_exception_handler(ConfigurationError, configuration_error_handler)
    app.add_exception_handler(DatasetLoadError, dataset_load_error_handler)
    app.add_exception_handler(ValidationRuntimeError, validation_runtime_error_handler)
    app.add_exception_handler(LLMProviderError, llm_provider_error_handler)
    # Generic catch-all to prevent raw tracebacks from leaking
    app.add_exception_handler(Exception, generic_exception_handler)
