import logging
from typing import Optional
from discord.ext import commands
from discord import Intents

class BaseBot(commands.AutoShardedBot):
    """
    Base class for a Discord bot using discord.py's AutoShardedBot.
    This class initializes the bot with a command prefix and intents and syncs commands on setup.
    """
    def __init__(self, command_prefix: str, intents: Intents, logger: Optional[logging.Logger] = None):
        super().__init__(command_prefix=command_prefix, intents=intents)
        if logger:
            self.logger = logger
            logger.info("BaseBot initialized")

    async def setup_hook(self) -> None:
        if hasattr(self, 'logger') and self.logger:
            self.logger.info("Running setup_hook: Syncing app commands...")
        
        await self.tree.sync()
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.info("Commands synced successfully!")

    async def on_ready(self):
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f'Bot connected as: {self.user} (ID: {self.user.id})')