import logging
import dataclasses
from typing import Dict, Any, Optional
from logging import Logger
from src.infrastructure.services.config.models import ApplicationSettings, BotSettings
from src.infrastructure.services.config.interfaces.protocols import MapperProtocol

class DiscordSettingsMapper(MapperProtocol):
    """Maps discord settings into ApplicationSettings.bot_settings"""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def can_map(self, data: Dict[str, Any]) -> bool:
        return bool(data.get("discord") or data.get("TOKEN"))

    def map(self, data: Dict[str, Any], settings: ApplicationSettings) -> ApplicationSettings:
        try:
            self.logger.debug(f"Mapping DiscordSettings from data: {data}")
            discord_config: Dict[str, Any] = data.get("discord", {})
            token = data.get("TOKEN")

            bot_settings = BotSettings(
                prefix=discord_config.get("prefix"),
                token=token,
                intents=discord_config.get("intents")
            )

            new_settings = dataclasses.replace(settings, bot_settings=bot_settings)
            self.logger.debug("BotSettings mapped and attached to ApplicationSettings")
            return new_settings
        except Exception as exc:
            self.logger.error(f"Failed to map BotSettings: {exc}")
            raise
