import yaml
from typing import Any
from pathlib import Path
from dotenv import load_dotenv


class SettingsManager:
    """
    Singleton that manages settings loaded from a YAML file.
    Allows access to nested keys using a dictionary structure.
    """
    _instance = None
    _config: dict = {}

    def __new__(cls, yaml_config_path: Path = None):
        """
        Ensures only one instance of the class is created.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, yaml_config_path: Path = None):
        """
        Initializes the SettingsManager and loads the YAML config once.
        
        Args:
            yaml_config_path (Path): Path to the YAML configuration file.
        """
        if yaml_config_path and not self._config:
            yaml_config_path = Path(yaml_config_path)
            with open(yaml_config_path, 'r') as file:
                self._config = yaml.safe_load(file)

    def load_env(self, env_path: Path = Path(".env")) -> bool:
        """
        Loads environment variables from a .env file using dotenv.
        
        Args:
            env_path (Path): Path to the .env file. Defaults to Path(".env")
            
        Returns:
            bool: True if .env file was loaded successfully, False otherwise
            
        Raises:
            FileNotFoundError: If the .env file doesn't exist
        """
        env_path = Path(env_path)
        
        if not env_path.exists():
            raise FileNotFoundError(f"Environment file not found: {env_path}")
        
        loaded_env = load_dotenv(env_path)
        
        if not loaded_env:
            raise RuntimeError(f"Failed to load environment file: {env_path}")
        
        return loaded_env

    def get(self, keys: dict) -> Any:
        """
        Retrieves a value from the config using nested key access.
        
        Args:
            keys (dict): Dictionary representing the path to the desired key.
            Example: {"Key": {"key1": "value"}}
            
        Returns:
            Any: The value associated with the nested key, or None if not found.
        """
        def recursive_get(data, key):
            if isinstance(key, dict):
                key, next_key = next(iter(key.items()))
                return recursive_get(data.get(key, {}), next_key) if isinstance(data, dict) else None
            return data.get(key) if isinstance(data, dict) else None

        return recursive_get(self._config, keys)

    def get_section(self, section: dict) -> dict:
        """
        Retrieves a specific section from the config using nested key access.
        
        Args:
            section (dict): Dictionary representing the path to the desired section.
            Example: {"database": {"connection": None}} to get the connection section
            
        Returns:
            dict: The section data, or an empty dict if the section does not exist.
        """
        def recursive_get(data, key):
            if isinstance(key, dict):
                key, next_key = next(iter(key.items()))
                return recursive_get(data.get(key, {}), next_key) if isinstance(data, dict) else {}
            return data.get(key, {}) if isinstance(data, dict) else {}

        result = recursive_get(self._config, section)
        return result if isinstance(result, dict) else {}