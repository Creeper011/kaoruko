from logging import Logger
from discord.ext.commands import AutoShardedBot, Bot
from typing import Optional, Type
from src.infrastructure.services.config.models.application_settings import BotSettings
from src.infrastructure.services.discord.basebot import BaseBot

class BotFactory():
    """Provides a Factory to build the discord Bot"""
    def __init__(self, basebot: Type[BaseBot], logger: Optional[Logger]):
        """
        Initializes the BotFactory.

        Args:
            basebot (BaseBot): The base bot class or callable used to instantiate
                the Discord bot.
            logger (Optional[Logger]): Logger instance used by the bot. If None,
                logging will be disabled or handled internally by the bot.
        """
        self.basebot = basebot
        self.logger = logger

    def create_bot(self, settings: BotSettings) -> BaseBot: # NOTE: caso haja necessidade, separar por intents, prefix ao ínves do modelo completo
        """
        Creates and returns a configured Discord bot instance.

        Args:
            settings (BotSettings): Configuration object containing bot settings
                such as command prefix and intents.

        Returns:
            BaseBot: An instance of the configured Discord bot.
        """
        if settings.prefix is None:
            raise ValueError("Bot prefix must be set in settings.")
        if settings.intents is None:
            raise ValueError("Bot intents must be set in settings.")

        return self.basebot(command_prefix=settings.prefix, intents=settings.intents, logger=self.logger)