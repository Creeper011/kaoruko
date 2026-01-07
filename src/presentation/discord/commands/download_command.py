from discord.ext import commands
import discord
from src.application.usecases.download_usecase import DownloadUsecase
from src.application.dto.request.download_request import DownloadRequest
from discord import app_commands
class DownloadCog(commands.Cog):
    """Cog for download command."""

    def __init__(self, bot: commands.Bot, download_usecase: DownloadUsecase) -> None:
        self.bot = bot
        self.download_usecase = download_usecase

    @app_commands.command(name="download", description="Download a file from a URL")
    async def download(self, interaction: discord.Interaction, url: str) -> None:
        """Download command to download a file from a URL."""
        await interaction.response.defer()
        
        download_request = DownloadRequest(
            url=url,
            file_size_limit=self.download_settings.file_size_limit,
        )
        
        try:
            download_output = await self.download_usecase.execute(download_request)
            
            if download_output.file_url:
                await interaction.followup.send(f"File uploaded successfully: {download_output.file_url} (Size: {download_output.file_size} bytes)")
            elif download_output.file_path:
                await interaction.followup.send(file=discord.File(download_output.file_path), content=f"File downloaded successfully (Size: {download_output.file_size} bytes)")
            else:
                await interaction.followup.send("Download completed, but no file available.")
        
        except Exception as e:
            await interaction.followup.send(f"An error occurred during download: {str(e)}")