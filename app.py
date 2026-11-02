import logging
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from settings import settings
from logging_config import setup_logging
from request_logging import register_request_logging
from mcc_classifier import MccClassificationError, classify


setup_logging()
logger = logging.getLogger(__name__)

# FastAPI application configuration
app = FastAPI(
    title="MCC Classification Service",
    description="MCC Classification API",
    version="1.0.0"
)

register_request_logging(app)


class ClassifyRequest(BaseModel):
    url: str
    mcc: str
    scraped_content: str = ""
    client: str = "default"
    meta: dict[str, Any] = Field(default_factory=dict)


class MccResponse(BaseModel):
    claimed_mcc: str
    predicted_mcc: str
    mcc_match: bool
    first_digit_diff: bool
    risk: Any
    out_of_scope: bool


class ClassifyResponse(BaseModel):
    mcc_response: MccResponse
    mcc_prediction: dict[str, Any]
    url: str


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


@app.get("/api/clients", response_model=list[str])
async def list_clients():
    """Return the client configuration names available to the service."""
    return ["default"]


async def _classify_request(request: ClassifyRequest) -> ClassifyResponse:
    """Run classification for a validated HTTP request."""
    try:
        result = classify(
            url=request.url,
            mcc=request.mcc,
            scraped_content=request.scraped_content,
            client=request.client,
            meta=request.meta,
        )
    except MccClassificationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    return ClassifyResponse.model_validate(result)


@app.post("/api/mcc/classify", response_model=ClassifyResponse)
async def classify_mcc(request: ClassifyRequest) -> ClassifyResponse:
    """Classify a website using the current API endpoint."""
    return await _classify_request(request)


@app.post("/classify", response_model=ClassifyResponse)
async def classify_legacy(request: ClassifyRequest) -> ClassifyResponse:
    """Classify a website using the legacy endpoint."""
    return await _classify_request(request)


@app.post("/run")
async def run_batch():
    """Reserve the batch endpoint for the Phase 7 batch workflow."""
    raise HTTPException(
        status_code=501,
        detail="Batch processing is not implemented until Phase 7",
    )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=settings.PORT,
    )