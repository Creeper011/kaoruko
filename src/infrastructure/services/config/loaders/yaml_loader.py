import yaml
from pathlib import Path
from typing import Dict, Any
from logging import Logger
from src.domain.exceptions.config_exceptions import YamlFailedLoad
from src.core.constants import DEFAULT_YAML_CONFIG_PATH, YAML_FILE_ENCODING

class YamlLoader():
    """Loader for yaml files"""

    def __init__(self, logger: Logger, config_path: Path = DEFAULT_YAML_CONFIG_PATH) -> None:
        self.logger: Logger = logger
        self.config_path: Path = config_path

    def load(self) -> Dict[str, Any]:
        """Loads yaml file and return their data."""
        
        try:
            with open(file=self.config_path, mode="r", encoding=YAML_FILE_ENCODING) as file:
                data = yaml.safe_load(file) or {}
                self.logger.debug(f"Successfully loaded yaml file on: {self.config_path}")
                return data
        except FileNotFoundError:
            msg: str = f"Yaml file not found: {self.config_path}"
            self.logger.error(msg)
            raise YamlFailedLoad(msg)
        
        except yaml.YAMLError as error:
            msg: str = f"Error on loading yaml file: {error}"
            self.logger.error(msg)
            raise YamlFailedLoad(msg)