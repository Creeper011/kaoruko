import logging
from logging import Logger
from typing import Any, Dict, Set
from pathlib import Path
from discord import Intents
from dacite import from_dict, Config
from src.services.config.interfaces import ConfigLoader
from src.services.config.models import ApplicationSettings


def _intents_hook(value: Any) -> Intents:
    intents_list = value if isinstance(value, list) else [value] if value else []
    intents = Intents.none()
    for intent_name in intents_list:
        if isinstance(intent_name, str):
            attr_name = intent_name.lower()
            if hasattr(intents, attr_name):
                setattr(intents, attr_name, True)
    return intents


class SettingsFactory():
    def __init__(self, logger: Logger | None, loaders: Set[ConfigLoader]) -> None:
        self.logger: Logger = logger or logging.getLogger(self.__class__.__name__)
        self.loaders: Set[ConfigLoader] = loaders

    def load_data(self) -> Dict[Any, Any]:
        all_data: Dict[str, Any] = {}
        for loader in self.loaders:
            all_data.update(loader.load())
        return all_data

    def build_settings(self) -> ApplicationSettings:
        raw_data = self.load_data()
        app_data = raw_data.get("application", raw_data)

        discord_config = app_data.get("discord", {})
        services_config = app_data.get("services", {})

        intents_list = discord_config.get("intents", [])
        intents = _intents_hook(intents_list)

        settings_data = {
            "discord": {
                "token": discord_config.get("token"),
                "prefix": discord_config.get("prefix"),
                "owner_id": discord_config.get("owner_id"),
                "intents": intents,
            },
            "download": services_config.get("download", {}),
            "drive": services_config.get("drive", {}),
        }

        app_settings = from_dict(
            data_class=ApplicationSettings,
            data=settings_data,
            config=Config(type_hooks={Path: Path})
        )

        self.logger.info("Application settings built successfully")
        return app_settings
