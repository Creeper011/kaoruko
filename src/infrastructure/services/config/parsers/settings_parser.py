from discord import Intents
from logging import Logger
from typing import Dict, Any
from copy import deepcopy

class SettingsParser():
    """Parse all keys from configuration to real objects"""

    def __init__(self, logger: Logger) -> None:
        self.logger: Logger = logger

    def _parse_intents(self, intents_config: Dict[str, bool]) -> Intents:
        """Parse all discord intents"""

        intents = Intents.none()
        for intent_name, enabled in intents_config.items():
            if not isinstance(enabled, bool) or not enabled:
                continue

            try:
                setattr(intents, intent_name, True)
                self.logger.debug(f"Activated intent: {intent_name}")
            except AttributeError:
                self.logger.warning(f"'{intent_name}' is not a valid intent. ignoring it")

        return intents

    def _parse_discord_config(self, discord_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse discord-specific configuration."""
        parsed_config = discord_config.copy()

        intents_dict = discord_config.get('intents')
        if isinstance(intents_dict, dict):
            intents_object = self._parse_intents(intents_dict)
            parsed_config['intents'] = intents_object
            self.logger.debug("Discord intents parsed successfully")

        return parsed_config

    def parse(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse all configuration keys into appropriate objects.

        Args:
            raw_config: Raw configuration dictionary from YAML/env

        Returns:
            New dictionary with parsed configuration objects
        """
        parsed_config = deepcopy(raw_config)

        discord_config = parsed_config.get('discord')
        if isinstance(discord_config, dict):
            parsed_config['discord'] = self._parse_discord_config(discord_config)
            self.logger.info("Discord configuration parsed successfully")
        else:
            self.logger.debug("No discord configuration found in config")

        return parsed_config