"""Base class to discord bot instance"""

import logging

from typing import Optional
from discord.ext import commands
from discord.activity import CustomActivity
from discord import Intents
from discord.gateway import DiscordWebSocket
from src.infrastructure.services.discord.utils.path_indentify import identify

class BaseBot(commands.AutoShardedBot):
    """
    Base class for a Discord bot using discord.py's AutoShardedBot.
    This class initializes the bot with a command prefix and intents and syncs commands on setup.
    """
    def __init__(self, command_prefix: str, intents: Intents, logger: Optional[logging.Logger] = None):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.info("BaseBot initialized")

    async def setup_hook(self) -> None:

        # NOTE: patch monkey to enable mobile status
        # (discord doesn't expose an method to use mobile status)
        DiscordWebSocket.identify = identify

        if hasattr(self, 'logger') and self.logger:
            self.logger.info("Running setup_hook: Syncing app commands...")

        self.logger.info("Bot info: %s (ID: %s)", self.user, self.user.id)
        await self.tree.sync()

        if hasattr(self, 'logger') and self.logger:
            self.logger.info("Commands synced successfully!")

    async def on_ready(self):
        if hasattr(self, 'logger') and self.logger:
            self.logger.info("Bot connected as: %s (ID: %s)", self.user, self.user.id)

        await self.change_presence(activity=CustomActivity(name="eating cakes.. yummy yummy"))
