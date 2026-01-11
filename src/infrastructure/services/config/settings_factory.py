from logging import Logger
from typing import Dict, Any, Set
from src.infrastructure.services.config.interfaces import ConfigLoader
from src.infrastructure.services.config.parsers import SettingsParser
from src.infrastructure.services.config.mappers import SettingsMapper
from src.infrastructure.services.config.models import ApplicationSettings

class SettingsFactory():
    """Orchestrates the creation of the ApplicationSettings object."""

    def __init__(self, logger: Logger, loaders: Set[ConfigLoader], parser: SettingsParser,
                 mapper: SettingsMapper) -> None:
        self.logger: Logger = logger
        self.loaders: Set[ConfigLoader] = loaders
        self.parser: SettingsParser = parser
        self.mapper: SettingsMapper = mapper

    def load_data(self) -> Dict[Any, Any]:
        all_data: Dict[str, Any] = {}
        for loader in self.loaders:
            all_data.update(loader.load())
        return all_data
    
    def build_settings(self) -> ApplicationSettings:
        """Builds the complete ApplicationSettings object by loading."""
        
        raw_data = self.load_data()
        parsed_data = self.parser.parse(raw_data)
        app_settings = self.mapper.map_data(parsed_data)
        
        self.logger.info("All processes to build application settings have occurred successfully with no errors.")
        return app_settings
