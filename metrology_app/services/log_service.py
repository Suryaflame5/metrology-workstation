"""
Structured Application Logging Service.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from ..config import LOGS_DIR, ensure_app_directories

_LOGGER = None


def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    ensure_app_directories()
    log_file = os.path.join(LOGS_DIR, "metrology.log")

    logger = logging.getLogger("MetrologyWorkstation")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    _LOGGER = logger
    return _LOGGER
