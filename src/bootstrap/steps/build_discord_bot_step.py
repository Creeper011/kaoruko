import logging
from typing import Any, Iterable, cast

from discord.ext.commands import Bot, Cog

from src.connectors.discord import BaseBot
from src.connectors.discord.extension_loader import ExtensionLoader
from src.connectors.discord.factories.bot_factory import BotFactory
from src.constants import DEFAULT_COMMANDS_PATH
from src.domain.models.settings import DiscordSettings
from src.services.module_finder import ModuleFinder


async def build_discord_bot(settings: DiscordSettings, extension_services: Iterable[Any]) -> BaseBot:
    """Builds Discord-related components."""
    logger = logging.getLogger("BuildDiscordBotStep")
    logger.info("Building Discord bot")

    bot = BotFactory(
        basebot=BaseBot,
        logger=logger,
    ).create_bot(settings=settings)

    module_finder = ModuleFinder(
        find_path=DEFAULT_COMMANDS_PATH,
        class_to_find=Cog,
    )
    cog_classes = module_finder.find_classes()

    extension_loader = ExtensionLoader(
        bot=cast(Bot, bot),
        extensions=cog_classes,
        services=extension_services,
    )

    await extension_loader.load_extensions()
    logger.info("Discord bot built successfully")
    return bot
