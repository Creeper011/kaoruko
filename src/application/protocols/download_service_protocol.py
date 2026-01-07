from typing import Protocol
from pathlib import Path
from src.domain.enum.formats import Formats

class DownloadServiceProtocol(Protocol):
    """Protocol for download service."""

    async def download(self, url: str, format_value: str | Formats, output_folder: Path) -> Path:
        """Download file from URL to output_folder."""
        ...