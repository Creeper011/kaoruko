import logging
from discord.ext.commands import Cog, Bot
from typing import Iterable, Any
from src.bootstrap.models import Compositor
from src.core.constants import DEFAULT_COMMANDS_PATH
from src.infrastructure.services.discord.extension_loader import ExtensionLoader
from src.infrastructure.filesystem.module_finder import ModuleFinder

class DiscordExtensionCompositor(Compositor):
    """Compositor Extension Loader system injecting their dependencies"""

    def __init__(self, *, bot: Bot, services: Iterable[Any]) -> None:
        self.bot = bot
        self.services = services
        self.logger = logging.getLogger(self.__class__.__name__)

    async def compose(self) -> None:
        """Load Extensions (Cogs) for discord"""
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
            services=self.services,
        )

        await extension_loader.load_extensions()