from typing import Dict, Optional
from pathlib import Path
from logging import Logger
from datetime import datetime
from src.application.models.cached_item import CachedItem
from src.application.protocols.cache_storage_protocol import CacheStorageProtocol


class CacheManager():
    """Manages cache logic without technical storage implementation."""
    
    def __init__(self, logger: Logger, storage: CacheStorageProtocol) -> None:
        self.logger = logger
        self.storage = storage
        self.cache_index: Dict[str, CachedItem] = {}
        
        self._load_cache()
        self.logger.info("CacheManager initialized successfully")
    
    def _load_cache(self) -> None:
        """Loads existing cache entries from storage."""
        try:
            raw_index = self.storage.load_index()
            self.cache_index = self._deserialize_index(raw_index)
            self.logger.debug(f"Loaded {len(self.cache_index)} cache entries")
        except Exception as error:
            self.logger.warning(f"Failed to load cache index: {error}")
            self.cache_index = {}
    
    def _deserialize_index(self, raw_index: Dict[str, Dict]) -> Dict[str, CachedItem]:
        """Converts raw dictionary to CachedItem objects."""
        result = {}
        for key, data in raw_index.items():
            result[key] = CachedItem(
                local_path=Path(data["local_path"]) if data.get("local_path") else None,
                remote_url=data.get("remote_url"),
                file_size=data.get("file_size"),
                last_accessed=data.get("last_accessed"),
                access_count=data.get("access_count", 0)
            )
        return result
    
    def _serialize_index(self) -> Dict[str, Dict]:
        """Converts CachedItem objects to serializable dictionary."""
        result = {}
        for key, item in self.cache_index.items():
            result[key] = {
                "local_path": str(item.local_path) if item.local_path else None,
                "remote_url": item.remote_url,
                "file_size": item.file_size,
                "last_accessed": item.last_accessed,
                "access_count": item.access_count
            }
        return result
    
    def _persist_index(self) -> None:
        """Saves current cache index to storage."""
        serialized = self._serialize_index()
        self.storage.save_index(serialized)
    
    def get(self, key: str) -> Optional[CachedItem]:
        """Retrieves item from cache with automatic validation and statistics update."""
        if key not in self.cache_index:
            self.logger.debug(f"Cache MISS for key: {key}")
            return None
        
        item = self.cache_index[key]
        
        if item.local_path and not self.storage.file_exists(item.local_path):
            self.logger.warning(f"Cached file missing: {item.local_path}")
            self._invalidate(key)
            return None
        
        self._update_access_stats(key)
        self.logger.debug(f"Cache HIT for key: {key}")
        
        return item
    
    def store(self, key: str, source_path: Path, file_size: Optional[int] = None, remote_url: Optional[str] = None) -> CachedItem:
        """Stores file in cache with metadata."""
        if not self.storage.file_exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if file_size is None:
            file_size = self.storage.get_file_size(source_path)
        
        persistent_path = self.storage.store_file(key, source_path, source_path.name)
        
        now = datetime.now().isoformat()
        item = CachedItem(
            local_path=persistent_path,
            remote_url=remote_url,
            file_size=file_size,
            last_accessed=now,
            access_count=0
        )
        
        self.cache_index[key] = item
        self._persist_index()
        
        self.logger.debug(f"Cached local file: {persistent_path}")
        return item

    def register_remote(self, key: str, remote_url: str, file_size: Optional[int] = None) -> CachedItem:
        """Registers remote URL in cache without local file."""
        now = datetime.now().isoformat()
        item = CachedItem(
            local_path=None,
            remote_url=remote_url,
            file_size=file_size,
            last_accessed=now,
            access_count=0
        )
        
        self.cache_index[key] = item
        self._persist_index()
        
        self.logger.debug(f"Registered remote URL for key: {key}")
        return item
    
    def _update_access_stats(self, key: str) -> None:
        """Updates access statistics for cache item."""
        if key in self.cache_index:
            item = self.cache_index[key]
            item.last_accessed = datetime.now().isoformat()
            item.access_count = (item.access_count or 0) + 1
            self._persist_index()
    
    def _invalidate(self, key: str) -> None:
        """Invalidates cache entry without removing physical file."""
        if key in self.cache_index:
            self.cache_index.pop(key)
            self._persist_index()
            self.logger.debug(f"Invalidated cache entry for key: {key}")