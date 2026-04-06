"""Logging configuration for JARVIS 2.0."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler

from .config import settings


def setup_logger(
    name: str = "jarvis",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logger with rich console output and file logging.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with rich formatting
    console_handler = RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=settings.debug,
        markup=True,
    )
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(message)s",
        datefmt="[%X]",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    log_file_path = log_file or settings.log_file
    if log_file_path:
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Global logger instance
logger = setup_logger()
