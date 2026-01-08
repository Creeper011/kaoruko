import logging
from logging import Logger

class LoggingSetup():
    """Handles the actual configuration of the logging system."""

    @staticmethod
    def configure(level: int = logging.INFO) -> Logger:
        """
        Configures the basic logging for the application.

        Args:
            level: The desired logging level (e.g., logging.INFO).
        """
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,  
        )
        return logging.getLogger()