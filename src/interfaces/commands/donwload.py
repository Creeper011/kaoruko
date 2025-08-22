import asyncio
import logging
from typing import Optional
import discord
import validators
import os
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from src.domain.usecases.download import DownloadUsecase
from src.domain.entities.download_entity import DownloadResult
from src.application.utils.error_embed import create_error
from src.application.constants import ErrorTypes

logger = logging.getLogger(__name__)

class DownloadCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="download", description="Download from multiple sites")
    @app_commands.choices(
        format=[
            app_commands.Choice(name="mp4", value="mp4"),
            app_commands.Choice(name="mp3", value="mp3"),
            app_commands.Choice(name="mkv", value="mkv"),
            app_commands.Choice(name="webm", value="webm"),
            app_commands.Choice(name="ogg", value="ogg"),
        ],
        quality = [
            app_commands.Choice(name="1440p / 320 kbps", value="[height=1440]_[abr=320]"),
            app_commands.Choice(name="1080p / 320 kbps", value="[height=1080]_[abr=320]"),
            app_commands.Choice(name="720p / 128 kbps", value="[height=720]_[abr=128]"),
            app_commands.Choice(name="480p / 64 kbps", value="[height=480]_[abr=64]"),
            app_commands.Choice(name="360p / 48 kbps", value="[height=360]_[abr=48]"),
    ])
    @app_commands.describe(url="A query or a url (Playlist not supported)",  format="The format to download", 
        invisible="If True, only you will see the result (ephemeral message)",
        speed="The speed to download the video (Min = 0.1, Max = 2.0)",
        preserve_pitch="If True, the pitch of the audio will be preserved",)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def download(self, interaction: discord.Interaction, url: str, format: app_commands.Choice[str] = "mp4",
                    quality: app_commands.Choice[str] = None,
                    speed: app_commands.Range[float, 0.1, 2.0] = None,
                    preserve_pitch: bool = False, invisible: bool = False):
        await interaction.response.defer(thinking=True, ephemeral=invisible)

        if speed == 1.0:
            speed = None

        if isinstance(format, app_commands.Choice):
            format = format.value

        if isinstance(quality, app_commands.Choice):
            quality = quality.value

        usecase = DownloadUsecase()

        try:
            download_result: DownloadResult = await usecase.download(url, format, speed, preserve_pitch, quality)

            if download_result.file_path and not download_result.drive_link:
                logger.debug(f"File downloaded successfully: {download_result.file_path}")
                path = Path(os.path.relpath(download_result.file_path))
                file = discord.File(path, filename=path.name)

                logger.debug(f"File converted to: {file.uri} | {file.filename}")
                await interaction.followup.send("Sending file...")

                elapsed = f"{download_result.elapsed:.2f}s"
                filesize = f"{os.path.getsize(download_result.file_path) / (1024*1024):.2f}MB"

                video_message = f"Resolution: {download_result.resolution}, Frame Rate: {download_result.frame_rate:.2f}fps"
                if download_result.speed_elapsed:
                    speed_elapsed = f"{download_result.speed_elapsed:.2f}s"
                    await interaction.edit_original_response(
                        content=f"Download Completed! Elapsed: {elapsed}, Speed Elapsed: {speed_elapsed}, Filesize: {filesize}\n{video_message if not download_result.is_audio else ''}",
                        attachments=[file]
                    )
                else:
                    await interaction.edit_original_response(
                        content=f"Download Completed! Elapsed: {elapsed}, Filesize: {filesize}\n{video_message if not download_result.is_audio else ''}",
                        attachments=[file]
                    )

            elif download_result.drive_link and not download_result.file_path:
                elapsed = f"{download_result.elapsed:.2f}s"

                if download_result.speed_elapsed:
                    speed_elapsed = f"{download_result.speed_elapsed:.2f}s"
                    await interaction.followup.send(
                        content=f"Download Completed! Elapsed: {elapsed}, Speed Elapsed: {speed_elapsed}\nLink: {download_result.drive_link}"
                    )
                else:
                    await interaction.followup.send(
                        content=f"Download Completed! Elapsed: {elapsed}\nLink: {download_result.drive_link}"
                    )


        except Exception as error:
            logger.error(f"Error occurred while downloading: {error}")
            await interaction.followup.send(embed=create_error(error="An error occurred while downloading the media.", type=ErrorTypes.UNKNOWN, code=str(error)))
            await asyncio.sleep(5)
            usecase._cleanup()
            return
        
        finally:
            await asyncio.sleep(1)  # Give some time for the file to be sent
            usecase._cleanup()

async def setup(bot: commands.Bot):
    """Load the Download cog."""
    await bot.add_cog(DownloadCog(bot))
