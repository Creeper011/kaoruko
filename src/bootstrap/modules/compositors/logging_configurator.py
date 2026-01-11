import logging

from src.bootstrap.models import Compositor
from src.bootstrap.modules.compositors.arg_parser import ArgParserCompositor
from src.bootstrap.modules.builders.logging_builder import LoggingBuilder

class LoggingConfigurator(Compositor):
    """Orchestrates the logging configuration."""

    def __init__(self, arg_parser_compositor: ArgParserCompositor, logging_builder: LoggingBuilder) -> None:
        self._arg_parser_compositor = arg_parser_compositor
        self._logging_builder = logging_builder

    def compose(self) -> None:
        """
        Parses command-line arguments and configures the application's
        logging level.
        """
        cli_args = self._arg_parser_compositor.compose()

        log_level = logging.INFO
        if cli_args.debug:
            log_level = logging.DEBUG
        
        # Recreate logging builder with the determined level
        self._logging_builder = LoggingBuilder(level=log_level)
        logger = self._logging_builder.build()
        
        discord_http_logger = logging.getLogger("discord.http")
        discord_http_logger.setLevel(logging.WARNING)
        discord_gateway_logger = logging.getLogger("discord.gateway")
        discord_gateway_logger.setLevel(logging.WARNING)

        logger.info(f"Logging configured with level: {logging.getLevelName(log_level)}")