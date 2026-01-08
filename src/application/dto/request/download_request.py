from dataclasses import dataclass
from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality

@dataclass(frozen=True)
class DownloadRequest:
    """Data transfer object for download request."""
    url: str
    file_size_limit: int
    format: Formats | None = None
    quality: Quality = Quality.DEFAULT