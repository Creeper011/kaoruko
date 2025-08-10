import logging
import discord
from discord.ext import commands
from discord import app_commands
from src.domain.usecases import SpeedControlMedia
from src.infrastructure.bot.utils import create_error
from src.infrastructure.constants import ErrorTypes
from src.domain.entities import SpeedMediaResult
from src.core.models.result import Result

logger = logging.getLogger(__name__)

class SpeedControlCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.speed_control = SpeedControlMedia()

    @app_commands.command(name="speed", description="Change media speed of an uploaded file")
    @app_commands.describe(
        factor="Speed factor (e.g., 0.5 for half speed, 2.0 for double speed)",
        preserve_pitch="Set to True to keep the original pitch, or False to change pitch with speed",
        attachment="The media file to process",
        invisible="If True, only you will see the result (ephemeral message)")
    async def speed(self, interaction: discord.Interaction, factor: app_commands.Range[float, 0.1, 2.0], attachment: discord.Attachment, preserve_pitch: bool = False, invisible: bool = False):
        await interaction.response.defer(ephemeral=invisible)

        try:
            file_data = await attachment.read()
            
            result: Result = await self.speed_control.change_speed_from_stream(
                file_data=file_data,
                filename=attachment.filename,
                content_type=attachment.content_type,
                speed=factor,
                preserve_pitch=preserve_pitch
            )
            
            # Handle failure result
            if not result.ok:
                await interaction.followup.send(embed=create_error(
                    error=result.error,
                    type=result.error_type if hasattr(result, 'error_type') else ErrorTypes.UNKNOWN
                ))
                return
            
            speed_result: SpeedMediaResult = result.value
            
            # Handle the result based on whether file was uploaded to Drive
            if speed_result.drive_link:
                # File was uploaded to Drive due to size
                success_message = (
                    f"Factor: {factor}x\n"
                    f"Preserve pitch: {'Yes' if preserve_pitch else 'No'}, "
                    f"Elapsed time: {speed_result.elapsed:.2f} seconds, "
                    f"File size: {speed_result.file_size / (1024 * 1024):.2f}MB\n"
                    f"File uploaded to Drive: {speed_result.drive_link}"
                )
                await interaction.edit_original_response(content=success_message)
            else:
                # File can be sent directly to Discord
                if speed_result.filepath and speed_result.filepath.exists():
                    file = discord.File(
                        speed_result.filepath, 
                        filename=speed_result.filepath.name
                    )
                    
                    success_message = (
                        f"Factor: {factor}x\n"
                        f"Preserve pitch: {'Yes' if preserve_pitch else 'No'}, "
                        f"Elapsed time: {speed_result.elapsed:.2f} seconds, "
                        f"File size: {speed_result.file_size / (1024 * 1024):.2f}MB"
                    )
                    
                    try:
                        await interaction.edit_original_response(content=success_message, attachments=[file])
                    except Exception as e:
                        logger.error(f"Error sending processed file: {e}")
                        await interaction.followup.send(content=success_message, file=file)

        except FileNotFoundError as e:
            await interaction.followup.send(embed=create_error(
                error="File not found or could not be processed",
                type=ErrorTypes.FILE_NOT_FOUND
            ))
        except Exception as error:
            logger.error(f"Speed control error: {error}")
            await interaction.followup.send(embed=create_error(
                error="Failed to process audio file",
                code=str(error),
                type=ErrorTypes.UNKNOWN
            ))

async def setup(bot: commands.Bot):
    """Load the SpeedControl cog."""
    await bot.add_cog(SpeedControlCog(bot))
