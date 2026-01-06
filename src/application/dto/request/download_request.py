from dataclasses import dataclass

@dataclass(frozen=True)
class DownloadRequest():
    """Data transfer object for download request."""
    url: str
    file_size_limit: int