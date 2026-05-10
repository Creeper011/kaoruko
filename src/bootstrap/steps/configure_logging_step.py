import argparse
import logging
from logging import Logger

from src.constants import DEFAULT_DEBUG_FLAG


def configure_logging() -> Logger:
    """Configures logging."""
    cli_args = _parse_args()

    log_level = logging.INFO
    if cli_args.debug:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )

    discord_http_logger = logging.getLogger("discord.http")
    discord_http_logger.setLevel(logging.WARNING)
    discord_gateway_logger = logging.getLogger("discord.gateway")
    discord_gateway_logger.setLevel(logging.WARNING)

    logger = logging.getLogger("ConfigureLoggingStep")
    logger.info(f"Logging configured with level: {logging.getLevelName(log_level)}")
    return logger


def _parse_args() -> argparse.Namespace:
    """Parse cli."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        *DEFAULT_DEBUG_FLAG,
        action="store_true",
        help="Enable debug logging"
    )
    return parser.parse_args()
