
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from settings import settings
from mcc_classifier import classify
from mongo_store import save_success, save_failure

logger = logging.getLogger(__name__)


class DuplicateJob(Exception):
    """Raised when a unique_id is already being processed."""

    status_code = 409


class QueueFull(Exception):
    """Raised when the job queue reaches its limit."""

    status_code = 503


# Thread pool
executor = ThreadPoolExecutor(
    max_workers=settings.MAX_WORKER_THREADS
)

# Tracks active and queued unique IDs
running = set()

# Protects concurrent access to running
lock = threading.Lock()


def submit_job(job_id, unique_id, value):
    """
    Submit a classification job to the background executor.

    Raises:
        DuplicateJob: If unique_id is already active.
        QueueFull: If the configured job limit is reached.
    """

    with lock:
        if unique_id in running:
            raise DuplicateJob(
                f"Job already submitted: {unique_id}"
            )

        if len(running) >= settings.MAX_QUEUED_JOBS:
            raise QueueFull(
                "Maximum job queue capacity reached"
            )

        running.add(unique_id)

    try:
        future = executor.submit(
            _process,
            job_id,
            unique_id,
            value,
        )
        return future

    except Exception:
        # Remove ID if executor submission itself fails
        with lock:
            running.discard(unique_id)
        raise


def _process(job_id, unique_id, value):
    """
    Execute classification in a background thread.
    """

    try:
        result = classify(**value)

        save_success(
            job_id,
            unique_id,
            result,
        )

    except Exception as exc:
        logger.exception(
            "Background classification failed: %s",
            unique_id,
        )

        try:
            save_failure(
                job_id,
                unique_id,
                str(exc),
            )
        except Exception:
            logger.exception(
                "Could not save job failure: %s",
                unique_id,
            )

    finally:
        with lock:
            running.discard(unique_id)

        logger.info(
            "Job removed from running set: %s",
            unique_id,
        )
