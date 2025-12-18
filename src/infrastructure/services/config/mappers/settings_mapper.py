from typing import Dict, Any
from logging import Logger
from src.infrastructure.services.config.models import ApplicationSettings, BotSettings

class SettingsMapper:
    """Maps a parsed configuration dictionary to a final ApplicationSettings object."""
    
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
    
    def _map_bot_settings(self, discord_config: Dict[str, Any]) -> BotSettings:
        """Maps discord configuration to BotSettings object."""
        try:
            bot_settings = BotSettings(
                prefix=discord_config.get('prefix'),
                token=discord_config.get('token'),
                intents=discord_config.get('intents')
            )
            self.logger.debug("BotSettings mapped successfully")
            return bot_settings
        except Exception as e:
            self.logger.error(f"Failed to map BotSettings: {e}")
            raise
    
    def map(self, parsed_data: Dict[str, Any]) -> ApplicationSettings:
        """Performs the mapping logic."""
        discord_config = parsed_data.get('discord', {})
        bot_settings = self._map_bot_settings(discord_config)

        app_settings = ApplicationSettings(bot_settings=bot_settings)
        
        self.logger.info("ApplicationSettings mapped successfully")
        return app_settings