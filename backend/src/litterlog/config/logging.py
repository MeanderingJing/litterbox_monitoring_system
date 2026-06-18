import logging
import os
from datetime import datetime


def _get_log_level() -> int:
    """Resolve the log level from the LOG_LEVEL environment variable."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def _should_log_to_file() -> bool:
    """Determine whether logs should also be written to a file."""
    value = os.getenv("LOG_TO_FILE", "true").lower()
    return value in {"1", "true", "yes", "on"}


def _find_project_root() -> str:
    """Find the repository root by walking up for known marker files.

    Falls back to the parent of the litterlog package directory when no
    markers are found (e.g. in Docker where the package lives at /app/litterlog).
    """
    markers = (
        "docker-compose.yml",
        os.path.join("backend", "pyproject.toml"),
    )

    path = os.path.abspath(os.path.dirname(__file__))
    while True:
        for marker in markers:
            if os.path.isfile(os.path.join(path, marker)):
                return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent

    package_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.dirname(package_dir)


def _get_log_file_path() -> str:
    """Build the log file path from environment variables (if enabled)."""
    project_root = _find_project_root()
    default_log_dir = os.path.join(project_root, "logs")
    log_dir = os.getenv("LOG_DIR", default_log_dir)
    if not os.path.isabs(log_dir):
        log_dir = os.path.join(project_root, log_dir)
    log_filename = os.getenv(
        "LOG_FILE_NAME",
        f'litterbox_sync_{datetime.now().strftime("%Y%m%d")}.log',
    )
    return os.path.join(log_dir, log_filename)


def setup_logging():
    """Set up logging configuration for the entire project (level/destination configurable)."""

    handlers = [logging.StreamHandler()]

    if _should_log_to_file():
        log_file_path = _get_log_file_path()
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file_path))

    logging.basicConfig(
        level=_get_log_level(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    # Set third-party library log levels to WARNING to reduce noise
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str):
    """Get a logger for a specific module."""
    setup_logging()  # Ensure logging is set up
    return logging.getLogger(name)
