import inspect
from logging import Logger
from typing import Any, Dict, Type, Iterable
from discord.ext.commands import Bot, Cog
from src.infrastructure.filesystem.module_finder import ModuleFinder

class ExtensionLoader():
    """Class to load extensions (cogs) into the bot with dependency injection."""

    def __init__(self, logger: Logger, bot: Bot, extensions: Iterable[Type[Cog]], services: Dict[Type, Any]):
        """
        Initializes the ExtensionLoader.

        Args:
            bot (Bot): The bot instance.
            extensions (Cog): The extensions to load
            services (Dict[Type, Any]): A dictionary mapping service types to their instances.
        """
        self.bot = bot
        self.services = services
        self.extensions = extensions
        self.logger = logger
        self.logger.debug(f"ExtensionLoader initialized with {len(services)} services and {len(extensions)} extensions.")

    async def load_extensions(self) -> None:
        """Loads all provided cogs, resolving and injecting dependencies."""
        self.logger.info("Starting extension loading...")

        for cog_class in self.extensions:
            try:
                cog = self._instantiate_cog(cog_class)
                await self.bot.add_cog(cog)

                self.logger.debug(f"Successfully loaded extension {cog_class.__name__}")

            except Exception as error:
                self.logger.error(f"Failed to load extension {cog_class.__name__}: {error}", exc_info=True)

        self.logger.info("Finished loading extensions.")

    # um util
    def _instantiate_cog(self, cog_class: Type[Cog]) -> Cog:
        """Creates a cog instance resolving its constructor dependencies."""
        signature = inspect.signature(cog_class.__init__)
        dependencies: Dict[str, Any] = {}

        for name, param in signature.parameters.items():
            if name in ("self", "bot"):
                continue

            param_type = param.annotation

            if param_type not in self.services:
                raise TypeError(
                    f"Service '{param_type.__name__}' not registered "
                    f"for cog '{cog_class.__name__}'."
                )

            dependencies[name] = self.services[param_type]

        return cog_class(self.bot, **dependencies)