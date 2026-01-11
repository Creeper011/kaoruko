import logging
import dataclasses
from typing import Dict, Any, Optional
from logging import Logger
from pathlib import Path
from src.infrastructure.services.config.models import ApplicationSettings
from src.domain.models.settings.drive_settings import DriveSettings
from src.infrastructure.services.config.interfaces.protocols import MapperProtocol

class DriveSettingsMapper(MapperProtocol):
    """Maps Google Drive settings into ApplicationSettings.drive_settings"""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def can_map(self, data: Dict[str, Any]) -> bool:
        return "drive" in data

    def map(self, data: Dict[str, Any], settings: ApplicationSettings) -> ApplicationSettings:
        try:
            self.logger.debug(f"Mapping DriveSettings from data: {data}")
            drive_config: Dict[str, Any] = data.get("drive", {})

            credentials_path = drive_config.get("credentials_path")
            credentials_path_obj = Path(credentials_path) if credentials_path else None

            drive_settings = DriveSettings(
                credentials_path=credentials_path_obj,
                folder_id=drive_config.get("folder_id")
            )

            new_settings = dataclasses.replace(settings, drive_settings=drive_settings)
            self.logger.debug("DriveSettings mapped and attached to ApplicationSettings")
            return new_settings
        except Exception as exc:
            self.logger.error(f"Failed to map DriveSettings: {exc}")
            raise
