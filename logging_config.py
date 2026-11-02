
import logging
import sys

from settings import settings


# Application logging initialization
def setup_logging():
    """Configure the application-wide log level, format, and output."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),

        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),

        handlers=[
            logging.StreamHandler(sys.stdout)
        ],

        force=True
    )
