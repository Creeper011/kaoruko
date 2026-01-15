from pathlib import Path
from typing import Dict
from logging import Logger
from dotenv import dotenv_values, load_dotenv
from src.domain.exceptions import EnvFailedLoad
from src.core.constants import DEFAULT_ENV_CONFIG_PATH

class EnvLoader():
    """Loader for .env files"""

    def __init__(self, logger: Logger, config_path: Path = DEFAULT_ENV_CONFIG_PATH) -> None:
        self.logger: Logger = logger
        self.config_path: Path = config_path

    def load(self) -> Dict[str, str]:
        """Loads environment variables from a .env file."""

        if not self.config_path.exists():
            msg: str = f".env file not found at path: {self.config_path.resolve()}"
            self.logger.warning(msg)
            raise EnvFailedLoad(msg)

        try:
            self.logger.debug(f"Loading environment variables from: {self.config_path.resolve()}")
            load_dotenv(dotenv_path=self.config_path, override=True)

            raw_env_data = dotenv_values(self.config_path)

            env_data: Dict[str, str] = {
                k: v for k, v in raw_env_data.items() if v is not None
            }

            self.logger.debug(f"Loaded {len(env_data)} variables from {self.config_path.name}")
            return env_data

        except Exception as e:
            msg: str = f"Error loading .env file: {e}"
            self.logger.exception(msg)
            raise EnvFailedLoad(msg)