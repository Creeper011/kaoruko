import logging
from logging import Logger
from pathlib import Path
from typing import Set
from src.infrastructure.filesystem.module_finder import ModuleFinder
from src.infrastructure.services.config.interfaces import MapperProtocol
from src.core.constants import DEFAULT_MAPPERS_PATH

class MapperFinder():
    """A class to automatically find any mapper in the mappers directory"""

    def __init__(self, logger: Logger, mapper_path: Path = DEFAULT_MAPPERS_PATH) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.mapper_path = mapper_path

    def find_loader_classes(self) -> Set[MapperProtocol]:
        """Find all mappers classes in the given path"""
        module_finder = ModuleFinder(
            self.logger, self.mapper_path, MapperProtocol
        )

        mapper_classes = module_finder.find_classes()
        return {mapper() for mapper in mapper_classes}