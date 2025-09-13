import discord
from discord.ext import commands
from discord import app_commands
from src.infrastructure.services.drive.drive_loader import DriveLoader
from src.application.utils.error_embed import create_error
from src.application.constants import ErrorTypes

class OwnerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="cleanup_drive")
    async def cleanup_drive(self, context: commands.Context):
        drive = DriveLoader().get_drive()
        try: 
            await drive.deleteAllFiles()
            await context.send("Drive cleaned up")
        except Exception as e:
            await context.send(embed=create_error(error=str(e), type=ErrorTypes.UNKNOWN))

async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCommands(bot))