import logging
from logging import Logger

class LoggingBuilder():
    """Builds the actual configuration of the logging system."""

    def __init__(self, level: int = logging.INFO) -> None:
        self.level = level

    def build(self) -> Logger:
        """
        Configures the basic logging for the application.

        Args:
            level: The desired logging level (e.g., logging.INFO).
        """
        logging.basicConfig(
            level=self.level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,  
        )
        return logging.getLogger()