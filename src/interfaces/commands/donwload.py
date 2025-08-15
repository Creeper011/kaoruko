import logging
from typing import Optional
import discord
import validators
import os
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from src.core.models.result import Result
from src.interfaces.services.service_provider import ServiceProvider, DownloaderService, SpeedControlMedia
from src.infrastructure.bot.utils import create_error
from src.infrastructure.constants import ErrorTypes

logger = logging.getLogger(__name__)

class DownloadCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service_provider = ServiceProvider()
        self.FILE_SIZE_LIMIT = 120 * 1024 * 1024  # 120 MB

    async def _cleanup(self, download_service: DownloaderService, result: Optional[Result] = None, speed_control: Optional[SpeedControlMedia] = None):
        # fallback: if result is None, try the downloader_service temp cleanup
        if result is None:
            try:
                await download_service._cleanup_temp_files()
            except Exception as e:
                logger.error(f"Error during fallback cleanup: {e}")
            return

        # if we have a result, try to cleanup sent file and speed temp dir if present
        try:
            if getattr(result, "filepath", None):
                await download_service.cleanup_after_send(result.filepath)
        except Exception as e:
            logger.error(f"Error cleaning up sent file: {e}")

        try:
            temp_dir = getattr(getattr(result, "value", None), "temp_dir", None)
            if temp_dir is not None and speed_control is not None:
                await speed_control._cleanup_temp_dir(temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp dir: {e}")

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
            
        if not validators.url(url):
            url = f"ytsearch:{url}"

        if isinstance(format, app_commands.Choice):
            format = format.value
        
        downloader_service = None
        try:
            # If speed is provided we want to keep the downloaded file locally so we can post-process it
            downloader_service = self.service_provider.get_downloader_service(url, format)
            download_result, result = await downloader_service.download(skip_drive_upload=(speed is not None))

            if not download_result or result is None:
                await interaction.followup.send("Download has been cancelled.")
                return
            
            if result.ok and download_result.is_success():
                # If speed is requested and we have a local file, apply speed processing
                if speed is not None and download_result.filepath:
                    speed_control = self.service_provider.get_speed_control_media()

                    # change_speed returns a Result containing SpeedMediaResult
                    speed_result = await speed_control.change_speed(Path(download_result.filepath), speed, preserve_pitch)

                    if not speed_result.ok:
                        await interaction.followup.send(embed=create_error(error=f"Speed processing failed: {speed_result.error}",
                                                                            type=ErrorTypes.UNKNOWN))
                        return

                    speed_value = speed_result.value

                    # If speed processing uploaded to Drive, report the link
                    if speed_value.drive_link:
                        await interaction.followup.send(
                            f"Download + speed completed! Download: {download_result.elapsed:.2f}s elapsed / Speed: {speed_value.elapsed:.2f}s elapsed.\nFile uploaded to Drive: {speed_value.drive_link}"
                        )
                        # cleanup original downloaded file and processed file
                        await self._cleanup(downloader_service, result, speed_control)
                        return

                    # Otherwise we have a local processed file
                    processed_path = speed_value.filepath
                    if not processed_path or not processed_path.exists():
                        await interaction.followup.send(embed=create_error(error="Processed file not found.", type=ErrorTypes.FILE_NOT_FOUND))
                        return

                    # Send file directly
                    file = discord.File(processed_path, filename=processed_path.name)
                    try:
                        await interaction.edit_original_response(
                            content=f"Download + speed completed! Download: {download_result.elapsed:.2f}s elapsed / Speed: {speed_value.elapsed:.2f}s elapsed.",
                            attachments=[file]
                        )
                    except Exception:
                        await interaction.followup.send(
                            f"Download + speed completed! Download: {download_result.elapsed:.2f}s elapsed / Speed: {speed_value.elapsed:.2f}s elapsed.",
                            file=file
                        )

                    # cleanup
                    await self._cleanup(downloader_service, result, speed_control)
                    if speed_value.temp_dir:
                        speed_control._cleanup_temp_dir(speed_value.temp_dir)
                    return

                # Handle file path when no speed requested
                if download_result.filepath:
                    if not os.path.exists(download_result.filepath):
                        await interaction.followup.send(embed=create_error(error="Download failed: File not found.", 
                                                                        type=ErrorTypes.FILE_NOT_FOUND))
                        return
                    
                    file_size = os.path.getsize(download_result.filepath)
                    if file_size > self.FILE_SIZE_LIMIT:
                        await interaction.followup.send(embed=create_error(error=f"File is too large: {file_size / (1024 * 1024):.2f}MB", 
                                                                        type=ErrorTypes.FILE_TOO_LARGE))
                        return
                    
                    await interaction.followup.send("Sending file...")
                    file = discord.File(download_result.filepath, filename=os.path.basename(download_result.filepath))
                    try:
                        await interaction.edit_original_response(
                            content=f"Download completed! {download_result.elapsed:.2f} seconds elapsed, {file_size / (1024 * 1024):.2f}MB.", 
                            attachments=[file]
                        )
                        await self._cleanup(downloader_service, result, None)
                    except Exception as e:
                        logger.error(f"Error sending file: {e}")
                        await interaction.followup.send(
                            f"Download completed! {download_result.elapsed:.2f} seconds elapsed, {file_size / (1024 * 1024):.2f}MB.", 
                            file=file
                        )
                        await self._cleanup(downloader_service, result, None)
                
                # Handle drive link (large files)
                elif download_result.link:
                    await interaction.followup.send(
                        f"Download completed! {download_result.elapsed:.2f} seconds elapsed.\n"
                        f"File uploaded to Drive: {download_result.link}"
                    )
                
                else:
                    await interaction.followup.send(embed=create_error(error="Download completed but no file or link available", 
                                                                    type=ErrorTypes.UNKNOWN))
            else:
                await interaction.followup.send(embed=create_error(error=f"Download failed: {result.error}", 
                                                                type=ErrorTypes.UNKNOWN))

        except Exception as error:
            logger.error(f"Download error: {error}")
            await interaction.followup.send(embed=create_error(error="Download failed", code=str(error), 
                                                               type=ErrorTypes.UNKNOWN))
            if downloader_service:
                await self._cleanup(downloader_service, locals().get("result", None), None)
        finally:
            if downloader_service:
                await downloader_service.schedule_cleanup(5)

async def setup(bot: commands.Bot):
    """Load the Download cog."""
    await bot.add_cog(DownloadCog(bot))
