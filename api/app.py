"""
FastAPI application factory.

Responsible only for creating the app, registering routers,
adding middleware, and defining lifecycle events.
"""

import logging
from contextlib import asynccontextmanager

import time
from fastapi import FastAPI

from api.exceptions import register_exception_handlers
from api.middleware import setup_middleware
from api.routes import router
from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    app.state.start_time = time.time()
    logger.info("FastAPI Application Started.")
    logger.info("Version: %s", getattr(settings, "APP_VERSION", "Unknown"))
    logger.info("Environment: %s", getattr(settings, "APP_ENVIRONMENT", "development"))
    yield
    logger.info("FastAPI Application Shutdown Initiated.")


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    tags_metadata = [
        {"name": "System", "description": "System health and configuration checks."},
        {"name": "Analytics", "description": "Execute the Forecast Review orchestration pipeline."},
        {"name": "Reporting", "description": "Retrieve previously generated reports."},
    ]

    app = FastAPI(
        title=getattr(settings, "APP_NAME", "Forecast Review API"),
        description="Enterprise API for the Forecast Review & Decision Support System. Provides a unified interface for deterministic analytics and AI narrative generation.",
        version=getattr(settings, "APP_VERSION", "1.0.0"),
        contact={
            "name": "Forecast Review Architecture Team",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=tags_metadata,
        lifespan=lifespan,
    )

    # Attach middlewares (CORS, Logging, Request ID)
    setup_middleware(app)

    # Register routers
    app.include_router(router)

    # Register custom exception handlers
    register_exception_handlers(app)

    # Mount static files for dashboard
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    
    dashboard_path = Path("dashboard")
    if dashboard_path.exists():
        app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

    return app

# The main application instance to be run via uvicorn
app = create_app()
