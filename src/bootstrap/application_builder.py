import logging
from typing import cast, Iterable, Any
from discord.ext.commands import Bot, AutoShardedBot
from src.bootstrap.models.application import Application
from src.bootstrap.modules.compositors import ArgParserCompositor, DiscordExtensionCompositor, LoggingConfigurator
from src.bootstrap.modules.builders import LoggingBuilder, SettingsBuilder, ExtensionServicesBuilder, DriveBuilder
from src.infrastructure.services.config.models import ApplicationSettings
from src.infrastructure.services.discord import BaseBot
from src.infrastructure.services.discord.factories.bot_factory import BotFactory
from src.infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService

class ApplicationBuilder:
    """Builds the application and all its runtime dependencies."""

    def __init__(self) -> None:
        self.logger: logging.Logger | None = None

    def _configure_logging(self) -> None:
        """Configures logging."""
        logging_configurator = LoggingConfigurator(
            arg_parser_compositor=ArgParserCompositor(),
            logging_builder=LoggingBuilder(),
        )
        logging_configurator.compose()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_settings(self) -> ApplicationSettings:
        """Builds application settings."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before building settings.")
        self.logger.info("Building application settings")

        return SettingsBuilder().build()

    async def _build_google_drive(self, settings: ApplicationSettings) -> GoogleDriveLoginService:
        """Builds Google Drive-related components."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before Google Drive components.")

        if settings.drive_settings is None:
            raise RuntimeError("Drive settings must be configured.")

        drive_login_service = await DriveBuilder(
            drive_settings=settings.drive_settings,
        ).build()

        self.logger.info("Google Drive login service built successfully")
        return drive_login_service

    def _build_extension_services(
        self, settings: ApplicationSettings, drive_login_service: GoogleDriveLoginService
    ) -> Iterable[Any]:
        """Builds services for extensions."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before building extension services.")

        self.logger.info("Building extension services")
        return ExtensionServicesBuilder(settings=settings, drive_login=drive_login_service).build()

    async def _build_discord(
        self, settings: ApplicationSettings, extension_services: Iterable[Any]
    ) -> BaseBot:
        """Builds Discord-related components."""
        if not self.logger:
            raise RuntimeError("Logger must be configured before Discord components.")

        if settings.bot_settings is None:
            raise RuntimeError("Bot settings must be configured.")

        self.logger.info("Building Discord bot")

        bot = BotFactory(
            basebot=BaseBot,
            logger=self.logger,
        ).create_bot(settings=settings.bot_settings)

        discord_compositor = DiscordExtensionCompositor(
            bot=cast(Bot, bot),
            services=extension_services,
        )

        await discord_compositor.compose()
        self.logger.info("Discord bot built successfully")
        return bot

    async def build(self) -> Application:
        """Builds the full application."""
        self._configure_logging()

        if not self.logger:
            raise RuntimeError("Logging configuration failed.")

        settings = self._build_settings()
        drive_login_service = await self._build_google_drive(settings)
        extension_services = self._build_extension_services(settings, drive_login_service)
        bot = await self._build_discord(settings, extension_services)

        if bot is None or settings is None or drive_login_service is None:
            raise RuntimeError("Application not fully built")

        self.logger.info("Assembling application")

        return Application(
            bot=cast(AutoShardedBot, bot),
            drive=drive_login_service,
            settings=settings,
        )
