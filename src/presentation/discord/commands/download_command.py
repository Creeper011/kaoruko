import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from src.application.usecases.download_usecase import DownloadUsecase
from src.application.dto.request.download_request import DownloadRequest
from src.domain.models.download_settings import DownloadSettings
from src.domain.enum.formats import Formats
from src.presentation.discord.factories import ErrorEmbedFactory
from src.core.constants import DEFAULT_DOWNLOAD_FORMAT

class DownloadCog(commands.Cog):
    """Cog for download command."""

    def __init__(self, bot: commands.Bot, download_usecase: DownloadUsecase, download_settings: DownloadSettings) -> None:
        self.bot = bot
        self.download_usecase = download_usecase
        self.download_settings = download_settings

    @app_commands.choices(format=[
        app_commands.Choice(name=format.value, value=format.value) for format in Formats
    ])
    @app_commands.command(name="download", description="Download a file from a URL")
    async def download(self, interaction: discord.Interaction, url: str, format: Choice[str] | None = DEFAULT_DOWNLOAD_FORMAT) -> None:
        """Download command to download a file from a URL."""
        await interaction.response.defer()
        
        file_size_limit = self._calculate_file_size_limit(interaction)
        
        if not file_size_limit:
            raise ValueError("Could not calculate file size limit for download.")
        
        if isinstance(format, Choice):
            format_enum = self._parse_format(format.value)
        else:
            format_enum = self._parse_format(format)
        
        if format and format_enum is None:
            await interaction.followup.send(f"Invalid format: {format}. Supported formats are: {', '.join([f.value for f in Formats])}")
            return
        
        download_request = DownloadRequest(
            url=url,
            format=format_enum,
            file_size_limit=file_size_limit
        )
        
        try:
            download_output = await self.download_usecase.execute(download_request)
            
            if download_output.file_url:
                await interaction.followup.send(f"File uploaded successfully: {download_output.file_url} (Size: {download_output.file_size} bytes)")
            elif download_output.file_path:
                await interaction.followup.send(file=discord.File(download_output.file_path), content=f"File downloaded successfully (Size: {download_output.file_size} bytes)")
            else:
                await interaction.followup.send("Download completed, but no file available.")
        
        except Exception as error:
            self.bot.logger.error(f"Unexpected error in download command: {error}", exc_info=error)
            embed = ErrorEmbedFactory.create_error_embed(error)
            await interaction.followup.send(embed=embed)

    def _calculate_file_size_limit(self, interaction: discord.Interaction) -> int:
        """Calculate the file size limit based on guild settings."""
        if interaction.guild:
            # Usa o maior entre o limite do servidor e o padrão
            return max(
                self.download_settings.file_size_limit,
                interaction.guild.filesize_limit
            )
        return self.download_settings.file_size_limit

    def _parse_format(self, format_str: str | None) -> Formats | None:
        """Parse format string to Formats enum."""
        if not format_str:
            return None

        try:
            return Formats(format_str)
        except ValueError:
            return None