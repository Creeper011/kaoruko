import os
import discord
import logging
from discord.ext import commands
from discord.gateway import DiscordWebSocket
from src.config import SettingsManager
from src.exceptions.bot.basebot_exceptions import *
from src.infrastructure.bot import ExtensionLoader
from src.infrastructure.bot.utils import identify

logger = logging.getLogger(__name__)

class Bot(commands.AutoShardedBot):
    def __init__(self, reconnect: bool = True):
        self.settings = SettingsManager()
        self.reconnect = reconnect
        self.intents_config = self.settings.get_section({"Bot": "intents"})
        self.prefix = self.settings.get({"Bot": "prefix"})
        intents = discord.Intents(**self.intents_config)

        self.custom_status_name = self.settings.get({"Bot": "custom_status_name"})
        self.status_value = self.settings.get({"Bot": "status"}) # expect: "online", "dnd", "offline", "idle"
        self.STATUS_MAP = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "offline": discord.Status.offline,
        }
        self.status_presence = self.STATUS_MAP.get(self.status_value.lower(), discord.Status.online)
        self.mobile_identify = self.settings.get({"Bot": "mobile_identify"})

        if isinstance(self.mobile_identify, bool):
            DiscordWebSocket.identify = identify
        else:
            logger.warning("mobile_identify value is invalid: expected a bool")

        super().__init__(command_prefix=self.prefix, intents=intents)

    async def on_ready(self):
        logger.info(f"{self.user} loaded")
        await ExtensionLoader(super()).load_extensions()
        await self.tree.sync()
        
        logger.debug(f"Status customization applied: Status: {self.status_presence.name}, Mobile: {self.mobile_identify}, Name: `{self.custom_status_name}")

        await self.change_presence(
            activity=discord.CustomActivity(name=self.custom_status_name , 
            emoji=discord.PartialEmoji(name="🍰")),
            status=self.status_presence)
        logger.info(f"commands synced")

    def run(self):
        token = os.getenv("TOKEN")
        if not token:
            raise EnvNotLoadedOrTokenNotFound("Not found TOKEN")
        super().run(token, reconnect=self.reconnect)