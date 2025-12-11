import logging
from typing import Optional


DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Configure logging once and return a module-specific logger."""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format=DEFAULT_LOG_FORMAT)
    return logging.getLogger(name or __name__)
