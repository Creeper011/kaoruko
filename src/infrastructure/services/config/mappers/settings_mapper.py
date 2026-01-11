import logging
from logging import Logger
from typing import Optional, Any, Dict
from src.infrastructure.services.config.models import ApplicationSettings
from src.infrastructure.services.config.interfaces.protocols import MapperProtocol

class SettingsMapper():
    """Maps all data in the json to a compreensive ApplicationSettings"""

    def __init__(self, mappers: set[MapperProtocol], logger: Optional[Logger] = None) -> None:
        self.mappers = mappers
        self.logger = logger or logging.getLogger(__name__)

    def map_data(self, all_data: Dict[str, Any]) -> ApplicationSettings:
        self.logger.debug("Starting settings mapping process")

        settings = ApplicationSettings()

        for mapper in self.mappers:
            if mapper.can_map(all_data):
                self.logger.debug(f"Applying mapper: {mapper.__class__.__name__}")
                settings = mapper.map(all_data, settings)

        self.logger.debug("Settings mapping completed")
        return settings