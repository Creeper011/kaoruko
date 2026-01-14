from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DownloadOutput():
    """Data transfer object for download output."""
    file_path: Path | None = None
    file_url: str | None = None
    file_size: int | None = None
    elapsed: float | None = None