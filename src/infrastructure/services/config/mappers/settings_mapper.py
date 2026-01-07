from typing import Dict, Any
from pathlib import Path
from logging import Logger
from src.infrastructure.services.config.models import ApplicationSettings, BotSettings
from src.domain.models.drive_settings import DriveSettings
from src.domain.models.download_settings import DownloadSettings   

class SettingsMapper:
    """Maps a parsed configuration dictionary to a final ApplicationSettings object."""
    
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
    
    def _map_bot_settings(self, parsed_data: Dict[str, Any]) -> BotSettings:
        """Maps discord configuration to BotSettings object."""
        try:
            self.logger.debug(f"Full data received for bot settings mapping: {parsed_data}")
            discord_config = parsed_data.get('discord', {})
            
            token = parsed_data.get('TOKEN')
            
            bot_settings = BotSettings(
                prefix=discord_config.get('prefix'),
                token=token,
                intents=discord_config.get('intents')
            )
            self.logger.debug("BotSettings mapped successfully")
            return bot_settings
        except Exception as e:
            self.logger.error(f"Failed to map BotSettings: {e}")
            raise
    
    def _map_download_settings(self, parsed_data: Dict[str, Any]) -> DownloadSettings:
        """Maps download configuration to DownloadSettings object."""
        try:
            self.logger.debug(f"Full data received for download settings mapping: {parsed_data}")
            download_config = parsed_data.get('download', {})
            
            download_settings = DownloadSettings(
                file_size_limit=download_config.get('file_size_limit', 25 * 1024 * 1024),
                blacklist_sites=download_config.get('blacklist_sites', [])
            )
            self.logger.debug("DownloadSettings mapped successfully")
            return download_settings
        except Exception as e:
            self.logger.error(f"Failed to map DownloadSettings: {e}")
            raise
    
    def _map_drive_settings(self, parsed_data: Dict[str, Any]) -> DriveSettings:
        """Maps drive configuration to DriveSettings object."""
        try:
            self.logger.debug(f"Full data received for drive settings mapping: {parsed_data}")
            drive_config = parsed_data.get('drive', {})
            
            drive_settings = DriveSettings(
                credentials_path=Path(drive_config.get('credentials_path')),
                folder_id=drive_config.get('folder_id')
            )
            self.logger.debug("DriveSettings mapped successfully")
            return drive_settings
        except Exception as e:
            self.logger.error(f"Failed to map DriveSettings: {e}")
            raise
        
    def map(self, parsed_data: Dict[str, Any]) -> ApplicationSettings:
        """Performs the mapping logic."""

        bot_settings = self._map_bot_settings(parsed_data)
        download_settings = self._map_download_settings(parsed_data)
        drive_settings = self._map_drive_settings(parsed_data)

        app_settings = ApplicationSettings(
            bot_settings=bot_settings,
            download_settings=download_settings,
            drive_settings=drive_settings
        )
        
        self.logger.info("ApplicationSettings mapped successfully")
        return app_settings