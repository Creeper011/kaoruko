import asyncio
import logging
import time
import discord
import os
from pathlib import Path
from discord.ext import commands
from discord import app_commands

from src.application.builderman import BuilderMan
from src.application.utils.error_embed import create_error
from src.application.constants import ErrorTypes
from src.domain.interfaces.dto.request.download_request import DownloadRequest
from src.domain.exceptions import (
    InvalidDownloadRequest,
    MediaFilepathNotFound,
    UnsupportedFormat,
    FileTooLarge,
    NetworkError,
    DriveUploadFailed
)

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
            app_commands.Choice(name="1440p / 320 kbps", value="[height<=1440]_[abr<=320]"),
            app_commands.Choice(name="1080p / 320 kbps", value="[height<=1080]_[abr<=320]"),
            app_commands.Choice(name="720p / 128 kbps", value="[height<=720]_[abr<=128]"),
            app_commands.Choice(name="480p / 64 kbps", value="[height<=480]_[abr<=64]"),
            app_commands.Choice(name="360p / 48 kbps", value="[height<=360]_[abr<=48]"),
        ]
    )
    @app_commands.describe(
        url="A query or a url (Playlist not supported)",
        format="The format to download",
        invisible="If True, only you will see the result (ephemeral message)",
        quality="The quality to download",
        should_transcode="Force transcoding even if not strictly necessary (may take longer) if true rather than remuxing when possible"
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
        should_transcode: bool = False,
    ):
        await interaction.response.defer(thinking=True, ephemeral=invisible)

        if isinstance(format, app_commands.Choice):
            format = format.value

        if isinstance(quality, app_commands.Choice):
            quality = quality.value

        request = DownloadRequest(
            url=url,
            format=format,
            quality=quality,
            should_transcode=should_transcode
        )
        if interaction.is_guild_integration():
            if interaction.guild.filesize_limit <= 25 * 1024 * 1024:
                request.file_limit = 120 * 1024 * 1024 
            else:
                request.file_limit = interaction.guild.filesize_limit
        else:
            request.file_limit = None
            
        usecase = self.builder.build_download_usecase()
        start_time = time.time()
        download_result = None

        try:
            logger.debug(
                f"Starting download: {url}, Format: {format}, Quality: {quality} | User name: {interaction.user.name}, User id: {interaction.user.id}"
            )

            download_result = await usecase.execute(request)
            total_elapsed = time.time() - start_time
            total_elapsed = f"{total_elapsed:.2f}s"

            logger.debug(f"Total time in this process is: {total_elapsed}")

            if download_result.drive_link:
                logger.debug(f"File uploaded to Drive successfully: {download_result.drive_link}")
                elapsed = f"{download_result.elapsed:.2f}s"
                filesize = f"{download_result.filesize / (1024*1024):.2f}MB"
                video_message = (
                    f"Resolution: {download_result.resolution}, Frame Rate: {download_result.frame_rate:.2f}fps"
                    if not download_result.is_audio else ""
                )
                await interaction.followup.send(
                    content=f"Download Completed! Download Elapsed: {elapsed}, Total Elapsed: {total_elapsed}, Filesize: {filesize}\n{video_message}\nLink: {download_result.drive_link}"
                )
            else:
                logger.debug(f"File downloaded successfully: {download_result.file_path}")
                path = Path(os.path.relpath(download_result.file_path))
                file = discord.File(path, filename=path.name)

                await interaction.followup.send("Sending file...")

                elapsed = f"{download_result.elapsed:.2f}s"
                filesize = f"{download_result.filesize / (1024*1024):.2f}MB"
                video_message = (
                    f"Resolution: {download_result.resolution}, Frame Rate: {download_result.frame_rate:.2f}fps"
                    if not download_result.is_audio else ""
                )

                await interaction.edit_original_response(
                    content=f"Download Completed! Download Elapsed: {elapsed}, Total Elapsed: {total_elapsed}, Filesize: {filesize}\n{video_message}",
                    attachments=[file]
                )

        except InvalidDownloadRequest as e:
            logger.warning(f"Invalid download request: {e}")
            await interaction.followup.send(
                embed=create_error(
                    error="Invalid download request.",
                    type=ErrorTypes.INVALID_INPUT,
                    note="Please check your URL and make sure it's valid.",
                    code=str(e)
                )
            )
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")
        
        except MediaFilepathNotFound as e:
            logger.error(f"Downloaded file not found: {e}")
            await interaction.followup.send(
                embed=create_error(
                    error="Download completed but file was not found.",
                    type=ErrorTypes.FILE_NOT_FOUND,
                    note="This might be a temporary issue. Please try again."
                )
            )
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")
        
        except FileTooLarge as e:
            logger.warning(f"File too large: {e}")
            await interaction.followup.send(
                embed=create_error(
                    error="File is too large to upload directly.",
                    type=ErrorTypes.FILE_TOO_LARGE,
                    note="The file will be uploaded to Google Drive instead."
                )
            )
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")
        
        except DriveUploadFailed as e:
            logger.error(f"Drive upload failed: {e}")
            await interaction.followup.send(
                embed=create_error(
                    error="Failed to upload to Google Drive.",
                    type=ErrorTypes.UNKNOWN,
                    note="The file was downloaded but couldn't be uploaded to Drive. Please try again."
                )
            )
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")
        
        except NetworkError as e:
            logger.error(f"Network error: {e}")
            await interaction.followup.send(
                embed=create_error(
                    error="Network connection error.",
                    type=ErrorTypes.UNKNOWN,
                    note="Please check your internet connection and try again."
                )
            )
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")
        
        except UnsupportedFormat as e:
            logger.warning(f"Unsupported format: {e}")
            await interaction.followup.send(
                embed=create_error(
                    error="Unsupported format requested.",
                    type=ErrorTypes.INVALID_FILE_TYPE,
                    note="Please try a different format (mp4, mp3, mkv, webm, ogg)."
                )
            )
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")
        
        except Exception as error:
            logger.error(f"Unexpected error occurred while downloading: {error}", exc_info=True)
            await interaction.followup.send(
                embed=create_error(
                    error="An unexpected error occurred while processing your request.",
                    type=ErrorTypes.UNKNOWN,
                    note="Please try again later or contact support if the issue persists.",
                    code=str(error)
                )
            )
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")

        finally:
            if download_result:
                await self._cleanup(download_result)
            else:
                logger.debug("No download result to clean up.")

    async def _cleanup(self, download_result):
        """Clean up resources after download."""
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