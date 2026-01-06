from typing import Protocol
from pathlib import Path
from src.application.models.cached_item import CachedItem

class CacheServiceProtocol(Protocol):
    """Protocol for cache service."""
    
    def get(self, key: str) -> CachedItem | None:
        """Retrieve a file from cache by key. Returns None if not found."""
        ...

    def set(self, key: str, file_path: Path | None, remote_url: str | None = None) -> None:
        """Store a file in cache with the given key."""
        ...
    
    async def save_local_file(self, temp_path: Path) -> Path:
        """Saves a local file to the cache from a temporary path."""
        ...