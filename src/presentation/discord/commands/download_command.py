from discord.ext import commands
import discord
from src.application.usecases.download_usecase import DownloadUsecase
from src.domain.models.download_settings import DownloadSettings    
from src.application.dto.request.download_request import DownloadRequest
from discord import app_commands
class DownloadCog(commands.Cog):
    """Cog for download command."""

    def __init__(self, download_usecase: DownloadUsecase, download_settings: DownloadSettings) -> None:
        self.download_usecase = download_usecase
        self.download_settings = download_settings

    @app_commands.command(name="download", description="Download a file from a URL")
    async def download(self, interaction: discord.Interaction, url: str) -> None:
        ...