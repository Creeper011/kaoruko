import logging
from logging import Logger
from pathlib import Path
from typing import Type, Set
from src.infrastructure.filesystem.module_finder import ModuleFinder
from src.infrastructure.services.config.interfaces import ConfigLoader
from src.core.constants import DEFAULT_LOADERS_PATH

class LoadersFinder():
    """A class to automatically find any config loader in the loaders directory"""

    def __init__(self, logger: Logger, loaders_path: Path = DEFAULT_LOADERS_PATH) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.loaders_path = loaders_path

    def find_loader_classes(self) -> Set[Type[ConfigLoader]]:
        """Find all loader classes in the given path"""
        module_finder = ModuleFinder(
            self.logger, self.loaders_path, ConfigLoader
        )
        return module_finder.find_classes()