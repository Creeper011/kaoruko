from logging import Logger
from discord.ext.commands import AutoShardedBot, Bot
from typing import Optional, Type
from src.domain.models.settings import DiscordSettings
from src.connectors.discord.basebot import BaseBot


class BotFactory():
    def __init__(self, basebot: Type[BaseBot], logger: Optional[Logger]):
        self.basebot = basebot
        self.logger = logger

    def create_bot(self, settings: DiscordSettings) -> BaseBot:
        if not settings.prefix:
            raise ValueError("Bot prefix must be set in settings.")
        if settings.intents is None:
            raise ValueError("Bot intents must be set in settings.")

        return self.basebot(command_prefix=settings.prefix, intents=settings.intents)