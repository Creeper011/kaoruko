from typing import Protocol
from pathlib import Path
from src.application.models.cached_item import CachedItem

class CacheServiceProtocol(Protocol):
    """Protocol for cache service."""

    def get(self, key: str) -> CachedItem | None: 
        """Retrieve a cached item by key.
        Args:
            key (str): The cache key (usually the URL).
        Returns:
            CachedItem | None: The cached item if found, else None.
        """
        ...
    def store(self, key: str, source_path: Path, file_size: int | None = None, remote_url: str | None = None) -> CachedItem: 
        """Persist a local file into the cache and return the CachedItem.
        Args:
            key (str): The cache key (usually the URL).
            source_path (Path): The local file path to store in cache.
            file_size (int | None): Optional file size in bytes.
            remote_url (str | None): Optional remote URL associated with the file.
        Returns:
            CachedItem: The cached item representing the stored file.
        """
        ...

    def register_remote(self, key: str, remote_url: str, file_size: int | None = None) -> CachedItem: 
        """Register a remote URL in the cache without a local file.
        Args:
            key (str): The cache key (usually the URL).
            remote_url (str): The remote URL to register.
            file_size (int | None): Optional file size in bytes.
        Returns:
            CachedItem: The cached item representing the remote file.
        """
        ...