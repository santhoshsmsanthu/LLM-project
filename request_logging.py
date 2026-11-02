
import logging
import time

from fastapi import FastAPI, Request


logger = logging.getLogger("request_logger")


# HTTP request logging middleware registration
def register_request_logging(app: FastAPI):
    """Attach request duration, status, and failure logging to an app."""
    @app.middleware("http")
    async def log_requests(request: Request, call_next):

        start_time = time.perf_counter()

        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)

            duration = time.perf_counter() - start_time

            logger.info(
                "%s %s | Status: %s | Duration: %.4f seconds",
                method,
                path,
                response.status_code,
                duration
            )

            return response

        except Exception:
            duration = time.perf_counter() - start_time

            logger.exception(
                "%s %s | Failed | Duration: %.4f seconds",
                method,
                path,
                duration
            )

            raise
