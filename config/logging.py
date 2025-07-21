import logging
import os
from datetime import datetime


def setup_logging():
    """Set up simple logging configuration for the entire project."""

    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(
                f'logs/litterbox_sync_{datetime.now().strftime("%Y%m%d")}.log'
            ),
            logging.StreamHandler(),  # Console output
        ],
    )

    # Set third-party library log levels to WARNING to reduce noise
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str):
    """Get a logger for a specific module."""
    return logging.getLogger(name)
