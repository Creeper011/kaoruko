import os
import logging
from discord.ext import commands
from src.application.bot.events.on_ready_event import OnReadyEvent
from ..service_provider_container import ServiceProviderContainer

logger = logging.getLogger(__name__)

class Bot(commands.AutoShardedBot):
    def __init__(self, settings, intents, prefix, custom_status_name, status_presence, mobile_identify, container: ServiceProviderContainer, reconnect=True):
        super().__init__(command_prefix=prefix, intents=intents)
        self.settings = settings
        self.custom_status_name = custom_status_name
        self.status_presence = status_presence
        self.mobile_identify = mobile_identify
        self.reconnect = reconnect
        self.container = container

    async def on_ready(self):
        """Handle bot ready event handler."""
        await OnReadyEvent(self).handle_on_ready()

    def run(self):
        token = os.getenv("TOKEN")
        if not token:
            raise ValueError("Not found TOKEN")
        super().run(token, reconnect=self.reconnect)