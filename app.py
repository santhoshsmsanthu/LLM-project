import logging

from fastapi import FastAPI

from settings import settings
from logging_config import setup_logging
from request_logging import register_request_logging


setup_logging()
logger = logging.getLogger(__name__)

# FastAPI application configuration
app = FastAPI(
    title="MCC Classification Service",
    description="MCC Classification API",
    version="1.0.0"
)

register_request_logging(app)


# Service health monitoring endpoint
@app.get("/health")
async def health_check():
    """Report whether the MCC classification service is running."""
    logger.info("Health check endpoint called")
    return {
        "status": "success",
        "message": "MCC Classification Service is running",
        "environment": settings.ENV
    }
