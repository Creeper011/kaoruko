from logging import Logger
from discord.ext.commands import Cog, Bot
from typing import Dict, Type, Any
from src.core.constants import DEFAULT_COMMANDS_PATH
from src.infrastructure.services.discord.extension_loader import ExtensionLoader
from src.infrastructure.filesystem.module_finder import ModuleFinder
from src.bootstrap.models.services import Services

class DiscordExtensionStartup():
    """Startup Extension Loader system injecting their dependencies"""

    def __init__(self, *, bot: Bot, logger: Logger) -> None:
        self.bot = bot
        self.logger = logger

    async def load_extensions(self, services: Dict[Type, Any]) -> None:
        module_finder = ModuleFinder(
            logger=self.logger,
            find_path=DEFAULT_COMMANDS_PATH,
            class_to_find=Cog,
        )
        cog_classes = module_finder.find_classes()

        extension_loader = ExtensionLoader(
            logger=self.logger,
            bot=self.bot,
            extensions=cog_classes,
            services=services,
        )

        await extension_loader.load_extensions()