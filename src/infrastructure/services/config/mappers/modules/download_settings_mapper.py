import logging
import dataclasses
from typing import Dict, Any, Optional
from logging import Logger
from src.infrastructure.services.config.models import ApplicationSettings
from src.domain.models.settings import DownloadSettings
from src.infrastructure.services.config.interfaces.protocols import MapperProtocol
from src.core.constants import DEFAULT_DOWNLOAD_FILESIZE_LIMIT, DEFAULT_DOWNLOAD_BLACKLIST_SITES

class DownloadSettingsMapper(MapperProtocol):
    """Maps download-related settings into ApplicationSettings.download_settings"""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def can_map(self, data: Dict[str, Any]) -> bool:
        return "download" in data

    def map(self, data: Dict[str, Any], settings: ApplicationSettings) -> ApplicationSettings:
        try:
            self.logger.debug(f"Mapping DownloadSettings from data: {data}")
            download_config: Dict[str, Any] = data.get("download", {})

            download_settings = DownloadSettings(
                file_size_limit=download_config.get("file_size_limit", DEFAULT_DOWNLOAD_FILESIZE_LIMIT),
                blacklist_sites=download_config.get("blacklist_sites", DEFAULT_DOWNLOAD_BLACKLIST_SITES)
            )

            new_settings = dataclasses.replace(settings, download_settings=download_settings)
            self.logger.debug("DownloadSettings mapped and attached to ApplicationSettings")
            return new_settings
        except Exception as exc:
            self.logger.error(f"Failed to map DownloadSettings: {exc}")
            raise
