from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIRECTORY = PROJECT_ROOT / "logs"

APP_LOG_FILE = LOGS_DIRECTORY / "app.log"
ERROR_LOG_FILE = LOGS_DIRECTORY / "errors.log"


def configure_logging() -> None:
    """
    Configure application and error log files.

    The function is safe to call more than once.
    """

    LOGS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s",
    )

    application_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    application_handler.setLevel(
        logging.INFO
    )

    application_handler.setFormatter(
        log_format
    )

    error_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    error_handler.setLevel(
        logging.ERROR
    )

    error_handler.setFormatter(
        log_format
    )

    root_logger.addHandler(
        application_handler
    )

    root_logger.addHandler(
        error_handler
    )