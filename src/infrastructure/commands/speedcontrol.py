import logging
import discord
import os
import uuid
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from src.domain.usecases.speed_audio import SpeedControlAudio
from src.infrastructure.bot.utils.error_embed import create_error, ErrorTypes
from src.domain.entities import SpeedAudioResult
from src.infrastructure.constants.result import Result

logger = logging.getLogger(__name__)

class SpeedControlCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.FILE_SIZE_LIMIT = 120 * 1024 * 1024  # 120 MB
        self.speed_control = SpeedControlAudio()

    @app_commands.command(name="speed", description="Change audio speed of an uploaded file")
    @app_commands.describe(
        factor="Speed factor (e.g., 0.5 for half speed, 2.0 for double speed)",
        preserve_pitch="Set to True to keep the original pitch, or False to change pitch with speed",
        attachment="The audio file to process",
        invisible="If True, only you will see the result (ephemeral message)")
    async def speed(self, interaction: discord.Interaction, factor: float, attachment: discord.Attachment, preserve_pitch: bool = False, invisible: bool = False):
        await interaction.response.defer(ephemeral=invisible)

        # Validate speed factor
        if factor <= 0.1 or factor > 10:
            await interaction.followup.send(embed=create_error(
                error="Speed factor must be between 0.1 and 10.0",
                type=ErrorTypes.INVALID_INPUT
            ))
            return

        if not attachment.content_type or not attachment.content_type.startswith("audio/"):
            await interaction.followup.send(embed=create_error(
                error="The uploaded file is not a supported audio file. Please upload an audio file.",
                type=ErrorTypes.INVALID_INPUT
            ))
            return

        try:
            temp_dir = Path("temp/speed_control")
            temp_dir.mkdir(parents=True, exist_ok=True)

            unique_id = str(uuid.uuid4())
            temp_dir = temp_dir / unique_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            input_path = temp_dir / attachment.filename
            await attachment.save(input_path)
            
            # Process the audio
            speed_result = await self.speed_control.change_speed_async(
                factor=factor,
                preserve_pitch=preserve_pitch,
                filepath=input_path
            )
            
            # Check file size
            file_size = os.path.getsize(speed_result.filepath)
            if file_size > self.FILE_SIZE_LIMIT:
                await interaction.followup.send(embed=create_error(
                    error=f"Processed file is too large: {file_size / (1024 * 1024):.2f}MB",
                    type=ErrorTypes.FILE_TOO_LARGE
                ))
                # Clean up
                if input_path.exists():
                    input_path.unlink()
                if speed_result.filepath.exists():
                    speed_result.filepath.unlink()
                return

            # Send the processed file
            await interaction.followup.send("Processing audio...")
            
            file = discord.File(
                speed_result.filepath, 
                filename=speed_result.filepath.name
            )
            
            # Mensagem de sucesso como texto simples
            success_message = (
                f"Factor: {factor}x\n"
                f"Preserve pitch: {'Yes' if preserve_pitch else 'No'}, "
                f"Elapsed time: {speed_result.elapsed:.2f} seconds, "
                f"File size: {file_size / (1024 * 1024):.2f}MB"
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
        finally:
            # Clean up temporary files
            try:
                if 'input_path' in locals() and input_path.exists():
                    input_path.unlink()
                if 'speed_result' in locals() and speed_result.filepath.exists():
                    speed_result.filepath.unlink()
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {e}")

async def setup(bot: commands.Bot):
    """Load the SpeedControl cog."""
    await bot.add_cog(SpeedControlCog(bot))
