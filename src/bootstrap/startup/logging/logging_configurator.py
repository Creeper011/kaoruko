import logging

from src.bootstrap.startup.arg_parser import ArgParser
from src.bootstrap.startup.logging.logging_setup import LoggingSetup

class LoggingConfigurator():
    """Orchestrates the logging configuration."""

    def __init__(self, arg_parser: ArgParser, logging_setup: LoggingSetup) -> None:
        self._arg_parser = arg_parser
        self._logging_setup = logging_setup

    def configure(self) -> None:
        """
        Parses command-line arguments and configures the application's
        logging level.
        """
        cli_args = self._arg_parser.parse_cli()

        log_level = logging.INFO
        if cli_args.debug:
            log_level = logging.DEBUG
        
        logger = self._logging_setup.configure(level=log_level)
        
        discord_http_logger = logging.getLogger("discord.http")
        discord_http_logger.setLevel(logging.WARNING)
        discord_gateway_logger = logging.getLogger("discord.gateway")
        discord_gateway_logger.setLevel(logging.WARNING)

        logger.info(f"Logging configured with level: {logging.getLevelName(log_level)}")