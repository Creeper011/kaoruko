"""This module defines all default costants.. normaly used as fallback values."""

from pathlib import Path

DEFAULT_YAML_CONFIG_PATH = Path("config.yaml")
YAML_FILE_ENCODING = "UTF-8"
DEFAULT_ENV_CONFIG_PATH = Path(".env")
DEFAULT_LOADERS_PATH = Path("src/infrastructure/services/config/loaders")
DEFAULT_COMMANDS_PATH = Path("src/presentation/discord/commands")
DEFAULT_DISCORD_RECONNECT = True
DEFAULT_DEBUG_FLAG = ("-d", "--debug")
CACHE_DIR = Path(".cache")
CACHE_INDEX_FILE = CACHE_DIR / "index.json"
DEFAULT_TEMP_DIR = Path(".temp")