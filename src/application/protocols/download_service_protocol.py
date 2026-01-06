from typing import Protocol
from pathlib import Path

class DownloadServiceProtocol(Protocol):
    """Protocol for download service."""
    
    async def download(self, url: str, output_folder: Path) -> Path:
        """Download file from URL to output_folder."""
        ...