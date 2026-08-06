"""
Stateless HTTP endpoints for the FastAPI layer.

Contains only routing logic and delegates business orchestration
to the injected ForecastReviewService.
"""

import logging
import shutil
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse

from api.dependencies import get_forecast_review_service
from api.schemas import ForecastReviewResponse, HealthResponse
from config import settings
from services.serialization import serialize_review_result
from llm.provider_registry import ProviderRegistry

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/dashboard/index.html")

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(request: Request):
    """Health check endpoint to verify system status and configuration."""
    start_time = getattr(request.app.state, "start_time", time.time())
    uptime = time.time() - start_time
    
    # Ensure providers are initialized for health check
    try:
        ProviderRegistry.build_provider_chain()
    except Exception as e:
        logger.error("Failed to initialize providers for health check: %s", e)
    
    return HealthResponse(
        status="OK",
        version=getattr(settings, "APP_VERSION", "Unknown"),
        primary_provider=getattr(settings, "PRIMARY_PROVIDER", "None"),
        secondary_provider=getattr(settings, "SECONDARY_PROVIDER", "None"),
        uptime=uptime,
        providers_telemetry=ProviderRegistry.get_registry_health()
    )


@router.post("/review", response_model=ForecastReviewResponse, tags=["Analytics"])
async def review_forecast(
    file: UploadFile = File(...),
    service=Depends(get_forecast_review_service),
):
    """
    Executes the full deterministic analytics and AI narrative pipeline.

    Accepts an uploaded dataset, validates the extension, writes to a temporary
    location, runs the review pipeline, serializes the JSON schema, and securely
    cleans up the temporary files before returning the structured response.
    """
    logger.info("Request Received: POST /review - File: %s", file.filename)

    if not file.filename:
        logger.warning("No file provided in the request.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided.",
        )

    # Validate file extension securely
    filename = file.filename
    suffix = Path(filename).suffix.lower()
    
    if suffix not in settings.SUPPORTED_EXTENSIONS:
        logger.warning("Unsupported file extension attempted: %s", suffix)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file extension. Allowed: {settings.SUPPORTED_EXTENSIONS}",
        )
        
    # Validate Content-Type
    allowed_content_types = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]
    if file.content_type not in allowed_content_types:
        logger.warning("Unsupported Content-Type attempted: %s", file.content_type)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported Content-Type. Allowed: {allowed_content_types}",
        )

    # Secure temp file handling and Size Validation
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    temp_dir = tempfile.mkdtemp(prefix="forecast_review_api_")
    temp_path = Path(temp_dir) / f"upload{suffix}"
    
    file_size = 0

    try:
        # Save upload to disk in chunks and validate size
        with temp_path.open("wb") as buffer:
            while chunk := file.file.read(8192):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    logger.warning("File size exceeded limit of 50MB.")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds the maximum upload size of 50MB.",
                    )
                buffer.write(chunk)
                
        if file_size == 0:
            logger.warning("Uploaded file is empty.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty or corrupted.",
            )
            
        logger.info("Pipeline Started for %s (Size: %d bytes)", filename, file_size)
        
        # Execute Orchestration
        # Output artifacts are written to the storage/runs hierarchy via StorageManager
        execution = service.run(input_path=temp_path)
        
        logger.info("Pipeline Completed. Serializing response...")

        # Serialize identical to json_report.py
        response_dict = serialize_review_result(execution)

        logger.info("Response Returned.")
        return response_dict

    finally:
        # Guaranteed cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info("Temporary files cleaned up.")


@router.get("/reports/{report_id}", tags=["Reporting"])
async def get_report(report_id: str):
    """Placeholder endpoint for future storage backends."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Report retrieval is not yet implemented.",
    )
