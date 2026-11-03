"""
Logging configuration for ChessReview Backend.
Provides clean, structured logging with timestamps, levels, and module names.
"""

import logging
import sys
from config import settings


def setup_logger(name: str = "chessreview") -> logging.Logger:
    """
    Initializes and configures a named logger instance.
    Ensures single handler configuration to prevent duplicate log lines.
    """
    logger = logging.getLogger(name)

    # Determine log level from settings
    level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Propagate to root only if not already handled
    logger.propagate = False
    return logger


# Default application logger
logger = setup_logger("chessreview")

