"""
Middleware components for the FastAPI presentation layer.

Provides request IDs, structured logging, execution timing, and CORS.
"""

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID header into every request and response."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Attach to request state for use by other middlewares or endpoints
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs the start and completion of HTTP requests with timing."""

    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.info(
            "Incoming request - ID: %s | Method: %s | Path: %s",
            request_id,
            request.method,
            request.url.path,
        )
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            
            logger.info(
                "Request completed - ID: %s | Status: %s | Time: %.4fs",
                request_id,
                response.status_code,
                process_time,
            )
            return response
        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.error(
                "Request failed - ID: %s | Time: %.4fs | Error: %s",
                request_id,
                process_time,
                str(e),
            )
            raise


def setup_middleware(app):
    """Attach all middlewares to the FastAPI application."""
    # CORS must be added via app.add_middleware explicitly
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # BaseHTTPMiddleware instances are executed in reverse order of addition
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
