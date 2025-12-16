import inspect
from logging import Logger
from typing import Any, Dict, Type
from discord.ext.commands import Bot
from src.infrastructure.filesystem.module_finder import ModuleFinder

class ExtensionLoader:
    """Functionality to load extensions (cogs) into the bot with dependency injection."""

    def __init__(self, logger: Logger, bot: Bot, extension_finder: ModuleFinder, services: Dict[Type, Any]):
        """
        Initializes the ExtensionLoader.

        Args:
            bot (Bot): The bot instance.
            services (Dict[Type, Any]): A dictionary mapping service types to their instances.
        """
        self.bot = bot
        self.services = services
        self.extension_finder = extension_finder
        self.logger = logger
        self.logger.info(f"ExtensionLoader initialized with {len(services)} services.")

    async def load_extensions(self) -> None:
        """Finds and loads all extensions, injecting dependencies."""
        self.logger.info("Starting to load extensions...")
        cogs_to_load = self.extension_finder.find_classes()

        for cog_class in cogs_to_load:
            try:
                signature = inspect.signature(cog_class.__init__)
                dependencies = {}

                for param_name, param in signature.parameters.items():
                    if param_name in ('self', 'bot'):
                        continue

                    param_type = param.annotation
                    if param_type in self.services:
                        dependencies[param_name] = self.services[param_type]
                    else:
                        raise TypeError(f"Service '{param_type.__name__}' not found for cog '{cog_class.__name__}'")

                cog_instance = cog_class(self.bot, **dependencies)
                await self.bot.add_cog(cog_instance)
                self.logger.info(f"Successfully loaded extension '{cog_class.__name__}'.")

            except Exception as e:
                self.logger.error(f"Failed to load extension '{cog_class.__name__}': {e}", exc_info=True)

        self.logger.info(f"Finished loading extensions. {len(cogs_to_load)} cogs were processed.")
