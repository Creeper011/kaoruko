import logging
import discord
import validators
import os
from discord.ext import commands
from discord import app_commands
from src.domain.usecases.downloadService import DownloaderService
from src.infrastructure.bot.utils.error_embed import create_error, ErrorTypes
from src.domain.entities import DownloadResult
from src.infrastructure.constants.result import Result

logger = logging.getLogger(__name__)

class DownloadCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.FILE_SIZE_LIMIT = 120 * 1024 * 1024  # 120 MB

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
    @app_commands.describe(url="A query or a url (Playlist not supported)",  format="The format to download", invisible="If True, only you will see the result (ephemeral message)")
    async def download(self, interaction: discord.Interaction, url: str, format: app_commands.Choice[str] = "mp4", invisible: bool = False):
        await interaction.response.defer(ephemeral=invisible)

        if not validators.url(url):
            url = f"ytsearch:{url}"

        if isinstance(format, app_commands.Choice):
            format = format.value
        
        try:
            downloader_service = DownloaderService(url, format, cancel_at_seconds=240)
            download_result, result = await downloader_service.download()

            if not download_result or result is None:
                await interaction.followup.send("Download has been cancelled.")
                return
                
            if result.ok:
                # Handle file path (large files that couldn't be uploaded to drive)
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
                    except Exception as e:
                        logger.error(f"Error sending file: {e}")
                        await interaction.followup.send(
                            f"Download completed! {download_result.elapsed:.2f} seconds elapsed, {file_size / (1024 * 1024):.2f}MB.", 
                            file=file
                        )
                
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

async def setup(bot: commands.Bot):
    """Load the Download cog."""
    await bot.add_cog(DownloadCog(bot))