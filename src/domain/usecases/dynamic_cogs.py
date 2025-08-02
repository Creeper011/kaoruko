from discord.ext import commands
from src.infrastructure.bot.load_extensions import ExtensionLoader
from src.infrastructure.constants.result import Result
from trashbin.create_error import ErrorTypes

class DynamicCogs:
    """Usecase for dynamic unload, reload, load cogs"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.extensionloader = ExtensionLoader(self.bot)

    async def unload_command(self, extension_name: str) -> Result:
        try:
            extension = await self.extensionloader.find_extension(extension_name)
            if extension in self.bot.extensions:
                await self.bot.unload_extension(extension)
                return Result.success(value=extension_name)
            else:
                return Result.failure(error="Extension not found",
                                      type=ErrorTypes.EXTENSION_NOT_FOUND)
        except Exception as error:
            return Result.failure(error=str(error),
                                  type=ErrorTypes.EXTENSION_UNLOAD_ERROR)

    async def load_command(self, extension_name: str) -> Result:
        try:
            extension = await self.extensionloader.find_extension(extension_name)
            if extension and extension not in self.bot.extensions:
                await self.bot.load_extension(extension)
                return Result.success(value=extension_name)
            return Result.failure(error="Extension already loaded?",
                                  type=ErrorTypes.EXTENSION_LOAD_ERROR)
        except Exception as error:
            return Result.failure(error=str(error),
                                  type=ErrorTypes.EXTENSION_LOAD_ERROR)

    async def reload_command(self, extension_name: str) -> Result:
        try:
            extension = await self.extensionloader.find_extension(extension_name)
            if extension and extension in self.bot.extensions:
                await self.bot.reload_extension(extension)
                return Result.success(value=extension_name)
            else:
                return Result.failure(error="Extension not found",
                                      type=ErrorTypes.EXTENSION_NOT_FOUND)
        except Exception as error:
            return Result.failure(error=str(error),
                                  type=ErrorTypes.EXTENSION_RELOAD_ERROR)