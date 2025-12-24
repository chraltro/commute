"""
Logging configuration for Oslo Commute Time Optimizer.
Sets up consistent logging across all modules.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from config import config


def setup_logging():
    """
    Configure logging for the application.
    Sets up both console and file handlers with appropriate formatting.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter if not config.DEBUG else detailed_formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if config.LOG_FILE:
        try:
            file_handler = RotatingFileHandler(
                config.LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {config.LOG_FILE}")
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")

    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

    logger.info(f"Logging initialized (level: {config.LOG_LEVEL})")


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(name)
