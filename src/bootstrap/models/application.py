from logging import Logger
from discord.ext.commands import Bot
from src.infrastructure.services.config.models.application_settings import ApplicationSettings

class Application():
    """Represents the entire application runtime"""

    def __init__(self, bot: Bot, settings: ApplicationSettings, logger: Logger) -> None:
        self.bot = bot
        self.settings = settings
        self.logger = logger

    async def run(self) -> None:
        """Runs the application"""
        if not self.bot or not self.settings:
            raise RuntimeError("Application has not been built. Call build_async() before running.")
        
        self.logger.info("Starting Discord bot...")
        await self.bot.start(token=self.settings.bot_settings.token)

    async def shutdown(self) -> None:
        self.logger.info("Starting shutdown process")
        if self.bot:
            await self.bot.close()