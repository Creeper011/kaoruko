import discord
from discord.ext import commands
from src.infrastructure.bot.load_extensions import ExtensionLoader
import os
import logging

logger = logging.getLogger(__name__)

class Bot(commands.AutoShardedBot):
    def __init__(self, settings, intents, prefix, custom_status_name, status_presence, mobile_identify, reconnect=True):
        super().__init__(command_prefix=prefix, intents=intents)
        self.settings = settings
        self.custom_status_name = custom_status_name
        self.status_presence = status_presence
        self.mobile_identify = mobile_identify
        self.reconnect = reconnect

    async def on_ready(self):
        logger.info(f"{self.user} loaded")
        await ExtensionLoader(super()).load_extensions()
        await self.tree.sync()        
        logger.debug(f"Status customization applied: Status: {self.status_presence.name}, Mobile: {self.mobile_identify}, Name: `{self.custom_status_name}")
        await self.change_presence(
            activity=discord.CustomActivity(name=self.custom_status_name, emoji=discord.PartialEmoji(name="🍰")),
            status=self.status_presence)
        logger.info(f"commands synced")

    def run(self):
        token = os.getenv("TOKEN")
        if not token:
            raise ValueError("Not found TOKEN")
        super().run(token, reconnect=self.reconnect)