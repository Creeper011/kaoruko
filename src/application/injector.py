import discord
import logging
import os
from pathlib import Path
from discord.gateway import DiscordWebSocket
from src.application.config import SettingsManager, LoggingSetup
from src.application.bot.utils import identify

logger = logging.getLogger(__name__)

class Injector:
    """Injector dependency for bot"""

    @staticmethod
    def inject(CONFIG_PATH_YAML: Path, ENV_PATH: Path, is_debug: bool):
        settings = SettingsManager(CONFIG_PATH_YAML)
        settings.load_env(ENV_PATH)
        logging = LoggingSetup(is_debug)
        intents = discord.Intents(**settings.get_section({"Bot": "intents"}))
        prefix = settings.get({"Bot": "prefix"})
        custom_status_name = settings.get({"Bot": "custom_status_name"})
        status_value = settings.get({"Bot": "status"})
        
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "offline": discord.Status.offline,
        }
        status_presence = status_map.get(status_value.lower(), discord.Status.online)

        mobile_identify = settings.get({"Bot": "mobile_identify"})
        if isinstance(mobile_identify, bool):
            DiscordWebSocket.identify = identify
        else:
            logger.warning("mobile_identify value is invalid: expected a bool")
        
        return {
            "settings": settings,
            "intents": intents,
            "prefix": prefix,
            "custom_status_name": custom_status_name,
            "status_presence": status_presence,
            "mobile_identify": mobile_identify
        }