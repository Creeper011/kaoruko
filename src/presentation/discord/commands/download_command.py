import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from src.application.protocols import DownloadUseCaseProtocol
from src.application.dto.request.download_request import DownloadRequest
from src.domain.models.settings.download_settings import DownloadSettings
from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality
from src.presentation.discord.factories import ErrorEmbedFactory
from src.core.constants import DEFAULT_DOWNLOAD_FORMAT

class DownloadCog(commands.Cog):
    """Cog for download command."""

    def __init__(self, bot: commands.Bot, download_usecase: DownloadUseCaseProtocol, download_settings: DownloadSettings) -> None:
        self.bot = bot
        self.download_usecase = download_usecase
        self.download_settings = download_settings

    @app_commands.choices(format=[
        app_commands.Choice(name=format.value, value=format.value) for format in Formats
    ])
    @app_commands.choices(quality=[
        app_commands.Choice(name=quality.value, value=quality.value) for quality in Quality
    ])
    @app_commands.command(name="download", description="Download a file from a URL")
    async def download(self, interaction: discord.Interaction, url: str, format: Choice[str] | None = DEFAULT_DOWNLOAD_FORMAT, quality: Choice[str] | None = None) -> None:
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
        
        if quality is None:
            quality_value = Quality.DEFAULT
        else:
            quality_value = Quality(quality.value)

        
        download_request = DownloadRequest(
            url=url,
            format=format_enum,
            file_size_limit=file_size_limit,
            quality=quality_value,
        )
        
        try:
            download_output = await self.download_usecase.execute(download_request)
            file_size_mb = self._bytes_to_megabytes(download_output.file_size) if download_output.file_size else "Unknown"
            elapsed = self._normalize_elapsed_time(download_output.elapsed)
            
            if download_output.file_url:
                content = f"Download Completed! {f"Download Elapsed: {elapsed}s" if elapsed else None}, Filesize: {file_size_mb} MB\nLink: {download_output.file_url}"
                await interaction.followup.send(content)
            elif download_output.file_path:
                content = f"Download Completed! {f'Elapsed: {elapsed}s' if elapsed else ''}, Filesize: {file_size_mb} MB"
                await interaction.followup.send(file=discord.File(download_output.file_path), content=content)
            else:
                content = "Download completed, but no file URL or path was provided."
                await interaction.followup.send(content)
        
        except Exception as error:
            self.bot.logger.error(f"Unexpected error in download command: {error}", exc_info=error)
            embed = ErrorEmbedFactory.create_error_embed(error)
            await interaction.followup.send(embed=embed)

    def _calculate_file_size_limit(self, interaction: discord.Interaction) -> int:
        """Calculate the file size limit based on guild settings."""
        return self.download_settings.file_size_limit

    def _normalize_elapsed_time(self, elapsed: float | None) -> float | None:
        """Normalize elapsed time to two decimal places."""
        if elapsed is None:
            return None
        return round(elapsed, 2)
    
    def _bytes_to_megabytes(self, bytes_size: int) -> int:
        """Convert bytes to megabytes."""
        return round(bytes_size / (1024 * 1024), 2)
    
    def _parse_format(self, format_str: str | None) -> Formats | None:
        """Parse format string to Formats enum."""
        if not format_str:
            return None

        try:
            return Formats(format_str)
        except ValueError:
            return None