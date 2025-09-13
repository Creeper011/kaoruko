import asyncio
import logging
import discord
import os
from pathlib import Path
from discord.ext import commands
from discord import app_commands

from src.application.builderman import BuilderMan
from src.application.utils.error_embed import create_error
from src.application.constants import ErrorTypes
from src.domain.interfaces.dto.request.download_request import DownloadRequest

logger = logging.getLogger(__name__)

class DownloadCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.builder = BuilderMan()

    @app_commands.command(name="download", description="Download from multiple sites")
    @app_commands.choices(
        format=[
            app_commands.Choice(name="mp4", value="mp4"),
            app_commands.Choice(name="mp3", value="mp3"),
            app_commands.Choice(name="mkv", value="mkv"),
            app_commands.Choice(name="webm", value="webm"),
            app_commands.Choice(name="ogg", value="ogg"),
        ],
        quality=[
            app_commands.Choice(name="1440p / 320 kbps", value="[height=1440]_[abr=320]"),
            app_commands.Choice(name="1080p / 320 kbps", value="[height=1080]_[abr=320]"),
            app_commands.Choice(name="720p / 128 kbps", value="[height=720]_[abr=128]"),
            app_commands.Choice(name="480p / 64 kbps", value="[height=480]_[abr=64]"),
            app_commands.Choice(name="360p / 48 kbps", value="[height=360]_[abr=48]"),
        ]
    )
    @app_commands.describe(
        url="A query or a url (Playlist not supported)",
        format="The format to download",
        invisible="If True, only you will see the result (ephemeral message)",
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def download(
        self,
        interaction: discord.Interaction,
        url: str,
        format: app_commands.Choice[str] = "mp4",
        quality: app_commands.Choice[str] = None,
        invisible: bool = False,
    ):
        await interaction.response.defer(thinking=True, ephemeral=invisible)

        if isinstance(format, app_commands.Choice):
            format = format.value

        if isinstance(quality, app_commands.Choice):
            quality = quality.value

        request = DownloadRequest(
            url=url,
            format=format,
            quality=quality
        )

        usecase = self.builder.build_download_usecase()

        download_result = None

        try:
            logger.debug(
                f"Starting download: {url}, Format: {format}, Quality: {quality}, "
                #f"Speed: {speed}, Preserve Pitch: {preserve_pitch}"
            )

            download_result = await usecase.execute(request)

            if download_result.drive_link:
                logger.debug(f"File uploaded to Drive successfully: {download_result.drive_link}")
                elapsed = f"{download_result.elapsed:.2f}s"
                await interaction.followup.send(
                    content=f"Download Completed! Elapsed: {elapsed}\nLink: {download_result.drive_link}"
                )
            else:
                logger.debug(f"File downloaded successfully: {download_result.file_path}")
                path = Path(os.path.relpath(download_result.file_path))
                file = discord.File(path, filename=path.name)

                await interaction.followup.send("Sending file...")

                elapsed = f"{download_result.elapsed:.2f}s"
                filesize = f"{os.path.getsize(download_result.file_path) / (1024*1024):.2f}MB"
                video_message = (
                    f"Resolution: {download_result.resolution}, Frame Rate: {download_result.frame_rate:.2f}fps"
                    if not download_result.is_audio else ""
                )

                await interaction.edit_original_response(
                    content=f"Download Completed! Elapsed: {elapsed}, Filesize: {filesize}\n{video_message}",
                    attachments=[file]
                )

        except Exception as error:
            logger.error(f"An unknown error occurred while downloading: {error}", exc_info=True)
            await interaction.followup.send(
                embed=create_error(
                    error="An unknown error occurred while processing your request.",
                    type=ErrorTypes.UNKNOWN,
                    code=str(error)
                )
            )

        finally:
            await asyncio.sleep(1)
            if download_result:
                if callable(download_result.cleanup):
                    if asyncio.iscoroutinefunction(download_result.cleanup):
                        await download_result.cleanup()
                    else:
                        download_result.cleanup()

async def setup(bot: commands.Bot):
    """Load the Download cog."""
    await bot.add_cog(DownloadCog(bot))