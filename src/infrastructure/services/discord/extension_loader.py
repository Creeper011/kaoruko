import inspect
from logging import Logger
from typing import Any, Dict, Type, Iterable
from discord.ext.commands import Bot, Cog

class ExtensionLoader():
    """Class to load extensions (cogs) into the bot with dependency injection."""

    def __init__(self, logger: Logger, bot: Bot, extensions: Iterable[Type[Cog]], services: Iterable[Any]):
        """
        Args:
            logger (Logger): Logger instance for logging.
            bot (Bot): The Discord bot instance.
            extensions (Iterable[Type[Cog]]): An iterable of Cog classes to be loaded.
            services (Iterable[Any]): A list or set of service instances.
        """
        self.bot = bot
        self.services = list(services)
        self.extensions = list(extensions)
        self.logger = logger
        self.logger.debug(f"ExtensionLoader initialized with {len(self.services)} services and {len(self.extensions)} extensions.")

    async def load_extensions(self) -> None:
        self.logger.info("Starting extension loading...")

        for cog_class in self.extensions:
            try:
                cog = self._instantiate_cog(cog_class)
                await self.bot.add_cog(cog)
                self.logger.debug(f"Successfully loaded extension {cog_class.__name__}")

            except Exception as error:
                self.logger.error(f"Failed to load extension {cog_class.__name__}: {error}", exc_info=True)

        self.logger.info("Finished loading extensions.")

    def _instantiate_cog(self, cog_class: Type[Cog]) -> Cog:
        signature = inspect.signature(cog_class.__init__)
        dependencies: Dict[str, Any] = {}

        for name, param in signature.parameters.items():
            if name in ("self", "bot"):
                continue

            param_type = param.annotation

            found_service = next(
                (service for service in self.services if isinstance(service, param_type)), 
                None
            )

            if found_service is None:
                raise TypeError(
                    f"Service of type '{param_type.__name__}' not found (registered) "
                    f"for cog '{cog_class.__name__}'."
                )

            dependencies[name] = found_service

        return cog_class(self.bot, **dependencies)
