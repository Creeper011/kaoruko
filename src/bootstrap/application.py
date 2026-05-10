import logging
from logging import Logger
from typing import Any, Callable, Iterable

from src.bootstrap.ascii_art import AsciiArt
from src.bootstrap.steps import (
    build_discord_bot,
    build_extension_services,
    build_settings,
    configure_logging,
    ensure_external_services,
)
from src.connectors.discord import BaseBot
from src.constants import DEFAULT_DISCORD_RECONNECT
from src.services.config.models import ApplicationSettings


class Application():
    """Represents the entire application runtime.
    Steps:
      1. First configure logging module
      2. Build settings
      3. Ensure external services
      4. Build Extensions discord
      5. Build discord
      6. Runs the application
    """

    def __init__(self) -> None:
        self.logger: Logger | None = None
        self.settings: ApplicationSettings | None = None
        self.extension_services: Iterable[Any] | None = None
        self.shutdown_callbacks: list[Callable[[], None]] = []
        self.bot: BaseBot | None = None
        self._is_built = False

    def _configure_logging(self) -> None:
        """Configures logging."""
        configure_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_settings(self) -> ApplicationSettings:
        """Builds application settings."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before building settings.")
        self.logger.info("Building application settings")

        return build_settings()

    async def _ensure_external_services(self, settings: ApplicationSettings) -> None:
        """Ensures external services are available."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before ensuring external services.")

        await ensure_external_services(settings=settings)

    async def _build_extension_services(self, settings: ApplicationSettings) -> tuple[Iterable[Any], list[Callable[[], None]]]:
        """Builds services for extensions."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before building extension services.")

        return await build_extension_services(settings=settings)

    async def _build_discord(self, settings: ApplicationSettings, extension_services: Iterable[Any]) -> BaseBot:
        """Builds Discord-related components."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before Discord components.")

        if settings.discord is None:
            raise RuntimeError("Bot settings must be configured.")

        bot = await build_discord_bot(
            settings=settings.discord,
            extension_services=extension_services,
        )

        return bot

    async def setup(self) -> None:
        """Builds the full application."""
        self._configure_logging()

        if not self.logger:
            raise RuntimeError("Logging configuration failed.")

        settings = self._build_settings()
        await self._ensure_external_services(settings)
        extension_services, shutdown_callbacks = await self._build_extension_services(settings)
        bot = await self._build_discord(settings, extension_services)

        if bot is None or settings is None:
            raise RuntimeError("Application not fully built")

        self.logger.info("Assembling application")

        self.settings = settings
        self.extension_services = extension_services
        self.shutdown_callbacks.extend(shutdown_callbacks)
        self.bot = bot
        self._is_built = True

    async def run(self) -> None:
        """Runs the application"""
        if not self._is_built:
            await self.setup()

        if not self.bot or not self.settings or not self.logger:
            raise RuntimeError("Application has not been built. Call setup() before running.")

        AsciiArt.print_ascii_art(self.logger)
        self.logger.info("Starting Discord bot...")
        try:
            if not self.settings.discord:
                raise ValueError("Bot settings are not configured in the application settings.")

            token = self.settings.discord.token
            if token is None:
                raise ValueError("Discord token is not set in the application settings.")

            await self.bot.start(token=token, reconnect=DEFAULT_DISCORD_RECONNECT)
        except (TypeError, ValueError) as error:
            self.logger.critical(
                "Could not start the application due the Discord Token is not valid. Make sure if you running the project in the correct root directory.",
                exc_info=error,
            )
        except Exception as error:
            self.logger.critical(
                "A critical error occurred during application Discord Bot startup",
                exc_info=error,
            )

    async def shutdown(self) -> None:
        logger = self.logger or logging.getLogger(self.__class__.__name__)
        logger.info("Starting shutdown process")
        if self.bot:
            logger.info("Closing discord bot connection")
            await self.bot.close()

        for callback in self.shutdown_callbacks:
            try:
                callback()
            except Exception as error:
                logger.error("Error during shutdown callback: %s", error)
