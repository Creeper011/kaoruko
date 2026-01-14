from typing import Protocol
from pathlib import Path
from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality
from src.domain.models import DownloadedFile

class DownloadServiceProtocol(Protocol):
    """Protocol for download service."""

    async def download(self, url: str, format_value: str | Formats, quality: Quality, output_folder: Path) -> DownloadedFile:
        """Download file from URL to output_folder."""
        ...