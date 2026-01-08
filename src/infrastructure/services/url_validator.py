import validators
import logging
from typing import Optional
from logging import Logger

class UrlValidator():
    """Service for validating URLs."""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def is_valid(self, url: str) -> bool:
        """Check if the provided URL is valid."""
        is_valid = validators.url(url)
        if is_valid:
            self.logger.debug(f"Valid URL: {url}")
        else:
            self.logger.warning(f"Invalid URL: {url}")
        return is_valid