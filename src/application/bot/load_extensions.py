import os
import logging
import time
from discord.ext import commands
from src.application.config.settings import SettingsManager

logger = logging.getLogger(__name__)

class ExtensionLoader():
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.extensions_path = SettingsManager().get({"Bot": "extensions_path"})
        if not self.extensions_path:
            raise ValueError("No extensions path configured in settings.")
        self.root_path = os.path.join(*self.extensions_path.split("."))

    async def find_extension(self, extension_name: str) -> str:
        """Find the extension path based on the given name.
        Args:
            extension_name (str): The name of the extension to find.
            Returns:
                str: The full path to the extension if found, otherwise None."""
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                if file == f"{extension_name}.py":
                    path = os.path.join(root, file)
                    extension_path = os.path.splitext(os.path.relpath(path, self.root_path))[0].replace(os.path.sep, ".")
                    return f"{self.extensions_path}.{extension_path}"
        return None
    
    async def load_extensions(self):
        """Load all extensions from the configured path."""
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.root_path) 
                    mod_path = os.path.splitext(rel_path.replace(os.sep, "."))[0]    
                    cog_path = f"{self.extensions_path}.{mod_path}"                     
                    if cog_path in self.bot.extensions:
                        continue
                    try:
                        start = time.perf_counter()
                        await self.bot.load_extension(cog_path)
                        elapsed = time.perf_counter() - start
                        logger.debug(f"Cog {cog_path} loaded in {elapsed:.3f} seconds")
                    except Exception as e:
                        logger.error(f"Error loading cog {cog_path}: {e}")
