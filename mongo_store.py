
import logging
from threading import Lock

from pymongo import MongoClient
from settings import settings

logger = logging.getLogger(__name__)

_client = None
_client_lock = Lock()


def get_db():
    """Create a MongoDB client once and return the application database."""
    global _client

    if _client is None:
        with _client_lock:
            if _client is None:
                if not settings.MONGODB_URI:
                    raise RuntimeError("MONGODB_URI is not configured")

                _client = MongoClient(
                    settings.MONGODB_URI,
                    serverSelectionTimeoutMS=5000,
                )

    return _client["MFApiServices"]


def close_mongo():
    """Close the MongoDB connection when the application shuts down."""
    global _client

    if _client is not None:
        _client.close()
        _client = None


def save_success(job_id, unique_id, result):
    """Save a successful MCC classification result."""

    if not isinstance(result, dict) or not result.get("url"):
        raise ValueError("Classification result must contain a URL")

    db = get_db()

    document_id = f"{result['url']}_{job_id}"

    document = {
        "_id": document_id,
        "url": result["url"],
        "job_id": job_id,
        "unique_id": unique_id,
        "item": {
            "Payload": result
        },
    }

    response = db["llm_mcc_pred_api"].replace_one(
        {"_id": document_id},
        document,
        upsert=True,
    )

    logger.info(
        "Classification saved: job_id=%s unique_id=%s "
        "matched=%s modified=%s upserted=%s",
        job_id,
        unique_id,
        response.matched_count,
        response.modified_count,
        response.upserted_id,
    )

    # Assumption: schedule records contain job_id and unique_id.
    schedule_result = db["job_schedule_api"].update_one(
        {
            "job_id": job_id,
            "unique_id": unique_id,
        },
        {
            "$set": {
                "status": 3,
            }
        },
    )

    logger.info(
        "Schedule status update: matched=%s modified=%s",
        schedule_result.matched_count,
        schedule_result.modified_count,
    )

    return document


def save_failure(job_id, unique_id, error):
    """Log a failed classification.

    Persistent failure storage can be added after confirming
    the required failure document schema and status codes.
    """
    logger.error(
        "Classification failed: job_id=%s unique_id=%s error=%s",
        job_id,
        unique_id,
        error,
    )
