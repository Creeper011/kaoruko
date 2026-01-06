from dataclasses import dataclass
from pathlib import Path

@dataclass
class CachedItem:
    local_path: Path
    remote_url: str | None = None
    file_size: int | None = None