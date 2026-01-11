import logging
from discord.ext.commands import AutoShardedBot
from src.core.constants import DEFAULT_DISCORD_RECONNECT
from src.infrastructure.services.config.models.application_settings import ApplicationSettings
from src.infrastructure.services.drive.google_drive_login_service import GoogleDriveLoginService
from src.utils import AsciiArt

class Application():
    """Represents the entire application runtime"""

    def __init__(self, bot: AutoShardedBot, drive: GoogleDriveLoginService,
                 settings: ApplicationSettings) -> None:
        self.bot = bot
        self.drive = drive
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def run(self) -> None:
        """Runs the application"""
        if not self.bot or not self.settings:
            raise RuntimeError("Application has not been built. Call build() before running.")
        
        AsciiArt.print_ascii_art(self.logger)
        self.logger.info("Starting Discord bot...")
        try:
            if not self.settings.bot_settings:
                raise ValueError("Bot settings are not configured in the application settings.")
            
            token = self.settings.bot_settings.token
            if token is None:
                raise ValueError("Discord token is not set in the application settings.")
            
            await self.bot.start(token=token, reconnect=DEFAULT_DISCORD_RECONNECT)
        except (TypeError, ValueError) as error:
            self.logger.critical("Could not start the application due the Discord Token is not valid. Make sure if you running the project in the correct root directory.",
            exc_info=error,
        )
        except Exception as error:
            self.logger.critical("A critical error occurred during application Discord Bot startup",
            exc_info=error,
        )

    async def shutdown(self) -> None:
        self.logger.info("Starting shutdown process")
        if self.bot:
            self.logger.info("Closing discord bot connection")
            await self.bot.close()
        if self.drive:
            self.drive.close_connection()