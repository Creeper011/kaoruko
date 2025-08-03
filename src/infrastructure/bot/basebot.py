import os
import discord
import logging
from discord.ext import commands
from src.config.settings import SettingsManager
from src.exceptions.bot.basebot_exceptions import *
from src.infrastructure.bot.load_extensions import ExtensionLoader

logger = logging.getLogger(__name__)

class Bot(commands.AutoShardedBot):
    def __init__(self, reconnect: bool = True):
        self.settings = SettingsManager()
        self.reconnect = reconnect
        self.intents_config = self.settings.get_section({"Bot": "intents"})
        self.prefix = self.settings.get({"Bot": "prefix"})
        intents = discord.Intents(**self.intents_config)
        super().__init__(command_prefix=self.prefix, intents=intents)

    async def on_ready(self):
        logger.info(f"{self.user} loaded")
        await ExtensionLoader(super()).load_extensions()
        await self.tree.sync()
        logger.info(f"All commands Synced")

    def run(self):
        token = os.getenv("TOKEN")
        if not token:
            raise EnvNotLoadedOrTokenNotFound("Not found TOKEN")
        super().run(token, reconnect=self.reconnect)