import discord
from discord.ext import commands
from discord import app_commands
from src.infrastructure.services.drive.drive_loader import DriveLoader
from src.application.utils.error_embed import create_error
from src.application.constants import ErrorTypes
import logging

logger = logging.getLogger(__name__)

class OwnerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="cleanup_drive")
    async def cleanup_drive(self, context: commands.Context):
        drive = DriveLoader().get_drive()
        try: 
            await drive.deleteAllFiles()
            await context.send("✅ Drive cleaned up successfully!")
        except Exception as e:
            logger.error(f"Unexpected error during drive cleanup: {e}", exc_info=True)
            await context.send(
                embed=create_error(
                    error="An unexpected error occurred during cleanup.",
                    type=ErrorTypes.UNKNOWN,
                    note="Please try again later or check the logs for more details.",
                    code=str(e)
                )
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCommands(bot))