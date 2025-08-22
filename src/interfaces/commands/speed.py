import discord
from discord.ext import commands
from discord import app_commands
from src.domain.usecases.speedmedia import SpeedMedia, SpeedMediaResult
from src.application.utils.error_embed import create_error
from src.application.constants import ErrorTypes

class SpeedCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.usecase = SpeedMedia()

    @app_commands.command(name="speed", description="Change speed")
    @app_commands.describe(attachment="The audio/video file to change speed", factor="The speed factor (0.1 - 2.0)", preserve_pitch="Whether to preserve pitch", invisible="Whether the response should be ephemeral")
    async def speedchange_command(self, interaction: discord.Interaction, attachment: discord.Attachment, 
                                factor: app_commands.Range[float, 0.1, 2.0], preserve_pitch: bool = False,
                                invisible: bool = None):
        await interaction.response.defer(thinking=True, ephemeral=invisible)

        result: SpeedMediaResult = await self.usecase.change_speed_attachment(attachment, factor, preserve_pitch)

        try:
            if result.file_path and not result.drive_path:
                await interaction.followup.send(content=f"Speed changed successfully! Speed: {factor}, Preserve Pitch: {preserve_pitch}, Elapsed: {result.elapsed:.2f}s", file=discord.File(result.file_path))
            else:
                await interaction.followup.send(content=f"Speed changed successfully! Speed: {factor}, Preserve Pitch: {preserve_pitch}, Elapsed: {result.elapsed:.2f}s\nLink: {result.drive_path}")
        except Exception as error:
            await interaction.followup.send(embed=create_error(error="", type=ErrorTypes.UNKNOWN, code=str(error)))
            self.usecase._cleanup()
            return
        
async def setup(bot: commands.Bot):
    await bot.add_cog(SpeedCog(bot))