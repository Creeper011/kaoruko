from dataclasses import dataclass

@dataclass(frozen=True)
class DownloadOutput():
    """Data transfer object for download output."""
    file_name: str | None = None
    file_bytes: bytes | None = None
    file_url: str | None = None
    file_size: int | None = None
    elapsed: float | None = None
