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
from src.infrastructure.bot.utils import create_error
from src.infrastructure.constants import ErrorTypes

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
        ]
    )
    @app_commands.describe(url="A query or a url (Playlist not supported)",  format="The format to download", 
        invisible="If True, only you will see the result (ephemeral message)",
        speed="The speed to download the video (Min = 0.1, Max = 2.0)",
        preserve_pitch="If True, the pitch of the audio will be preserved")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def download(self, interaction: discord.Interaction, url: str, format: app_commands.Choice[str] = "mp4", speed: app_commands.Range[float, 0.1, 2.0] = None,
                    preserve_pitch: bool = False, invisible: bool = False):
        await interaction.response.defer(thinking=True, ephemeral=invisible)
        
        if speed == 1.0:
            speed = None

        if isinstance(format, app_commands.Choice):
            format = format.value

        usecase = DownloadUsecase()

        try:
            download_result: DownloadResult = await usecase.download(url, format, speed, preserve_pitch)

            if download_result.file_path and not download_result.drive_link:
                file = discord.File(download_result.file_path)

                elapsed = f"{download_result.elapsed:.2f}s"
                filesize = f"{os.path.getsize(download_result.file_path) / (1024*1024):.2f}MB"

                if download_result.speed_elapsed:
                    speed_elapsed = f"{download_result.speed_elapsed:.2f}s"
                    await interaction.followup.send(
                        content=f"Download Completed! Elapsed: {elapsed}, Speed Elapsed: {speed_elapsed}, Filesize: {filesize}\nResolution: {download_result.resolution}, Frame Rate: {download_result.frame_rate:.2f}fps",
                        file=file
                    )
                else:
                    await interaction.followup.send(
                        content=f"Download Completed! Elapsed: {elapsed}, Filesize: {filesize}\nResolution: {download_result.resolution}, Frame Rate: {download_result.frame_rate:.2f}fps",
                        file=file
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
            usecase._cleanup()
            return
        
        finally:
            await asyncio.sleep(1)  # Give some time for the file to be sent
            usecase._cleanup()

async def setup(bot: commands.Bot):
    """Load the Download cog."""
    await bot.add_cog(DownloadCog(bot))
