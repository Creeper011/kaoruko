from pathlib import Path
from typing import Any, Dict
import logging
from logging import Logger
from yumly import Yumly, YumlyError
from src.constants import DEFAULT_YUMLY_CONFIG_PATH
from src.domain.exceptions import YumlyFailedLoad

class YumlyLoader():
    """Class to load yumly config files"""

    def __init__(self, logger: Logger | None = None, config_path: Path = DEFAULT_YUMLY_CONFIG_PATH) -> None:
        self.logger: Logger = logger or logging.getLogger(self.__class__.__name__)
        self.config_path: Path = config_path
        if Yumly is None:
            msg = "Yumly is not installed in the active Python environment."
            self.logger.error(msg)
            raise YumlyFailedLoad(msg)

        self.yumly: Yumly = Yumly()
        self.logger.debug("Yumly loader created for path: %s", self.config_path)

    def load(self) -> Dict[str, Any]:
        """Loads a yumly file and returns its data."""
        if not self.config_path.exists():
            msg: str = f"Yumly file not found at path: {self.config_path.resolve()}"
            self.logger.error(msg)
            raise YumlyFailedLoad(msg)

        try:
            self.logger.debug("Validating Yumly file at: %s", self.config_path.resolve())
            is_valid: bool = self.yumly.validate_file(str(self.config_path))
            if not is_valid:
                msg = f"Yumly validation failed for file: {self.config_path.resolve()}"
                self.logger.error(msg)
                raise YumlyFailedLoad(msg)

            self.logger.debug("Loading Yumly configuration from: %s", self.config_path.resolve())
            data = self.yumly.load(str(self.config_path))
            if not isinstance(data, dict):
                msg = f"Yumly file did not return a mapping: {self.config_path.resolve()}"
                self.logger.error(msg)
                raise YumlyFailedLoad(msg)

            return data

        except YumlyFailedLoad:
            raise
        except YumlyError as error:
            msg = f"Error loading Yumly file: {error}"
            self.logger.exception(msg)
            raise YumlyFailedLoad(msg) from error
