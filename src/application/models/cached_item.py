from dataclasses import dataclass
from pathlib import Path

@dataclass
class CachedItem():
    local_path: Path | None = None
    remote_url: str | None = None
    file_size: int | None = None
    created_at: str | None = None
    last_accessed: str | None = None
    access_count: int = 0