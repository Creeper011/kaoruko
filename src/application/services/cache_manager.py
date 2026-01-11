import logging
from typing import Dict, Optional, overload, Any
from pathlib import Path
from logging import Logger
from src.application.models.dataclasses.cached_item import CachedItem
from src.application.protocols.cache_storage_protocol import CacheStorageProtocol
from src.application.models.dataclasses.cache_key import CacheKey
from src.domain.models.result import Result
from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality
from src.core.constants import UNKNOWN_FILE_SIZE, DEFAULT_STRING_DIVISOR

class CacheManager():
    """Manages cache logic with a external interface CacheStorage"""
    
    def __init__(self, storage: CacheStorageProtocol, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.storage = storage

    async def _load_database_index(self) -> Dict[str, Dict[str, Any]]:
        self.logger.debug("Loading cache database index...")
        return await self.storage.load_index()

    async def _save_database_index(self, index: Dict[str, Dict[str, Any]]) -> Result:
        self.logger.debug("Saving cache database index...")
        try:
            await self.storage.save_index(index)
            return Result(ok=True)
        except Exception as error:
            self.logger.error(f"Failed to save cache index: {error}")
            return Result(ok=False, message=str(error), exception=error)

    async def get_item(self, key: CacheKey) -> Optional[CachedItem]:
        """Retrieves a cached item by its key.
        Args:
            key: (CacheKey) The indentifier to retrive
        Returns:
            CachedItem (Optional)
        """
        self.logger.debug(f"Retrieving cache item for key: {key}")
        index = await self._load_database_index()
        key_str = self._key_to_str(key)

        item_data = index.get(key_str)
        if not item_data:
            self.logger.debug(f"Cache MISS for key: {key}")
            return None

        self.logger.debug(f"Cache HIT for key: {key}")
        return self._deserialize_item({key_str: item_data})

    @overload
    async def store_item(self, key: CacheKey, source_file: Path, remote_url: None) -> CachedItem: ...

    @overload
    async def store_item(self, key: CacheKey, source_file: None, remote_url: str) -> CachedItem: ...

    async def store_item(self, key: CacheKey, source_file: Optional[Path], remote_url: Optional[str]) -> Optional[CachedItem]:
        """Index a item to cache
        Args:
            key: (CacheKey) The indentifier to store
            source_file: (Path) The file to index with the key
            remote_url: (str) The remote url to index with the key
        Returns:
            CachedItem (Optional) """
        self.logger.debug(f"Storing cache item for key: {key}")
        self.logger.debug(f"Original Source file: {source_file}, Remote URL: {remote_url}")    

        source_path = None
        key_str = self._key_to_str(key)

        if source_file and source_file.exists():
            self.logger.debug(f"Moving file to cache storage...")
            source_path = await self.storage.move_file_to_cache(key_str, source_file)

        file_size = source_path.stat().st_size if source_path else UNKNOWN_FILE_SIZE

        cached_item = CachedItem(
            key=key,
            local_path=source_path,
            remote_url=remote_url,
            file_size=file_size
        )

        index = await self._load_database_index()
        index.update(self._serialize_item(cached_item))
        result = await self._save_database_index(index)

        if not result.ok:
            self.logger.warning(f"Failed to save cache index: {result.message}")
            raise Exception(f"Failed to save cache index: {result.message}")

        self.logger.debug(f"Stored cache item: {cached_item}")
        return cached_item

    def _key_to_str(self, key: CacheKey) -> str:
        """Converts a CacheKey object to a unique string representation"""
        return f"{key.url}{DEFAULT_STRING_DIVISOR}{key.format_value.value}{DEFAULT_STRING_DIVISOR}{key.quality.value if key.quality else 'none'}"
    
    def _serialize_item(self, item: CachedItem) -> Dict[str, Dict[str, Any]]:
        """Converts a CachedItem object to a dict data"""
        return {
            self._key_to_str(item.key): {
                "local_path": str(item.local_path) if item.local_path else None,
                "remote_url": item.remote_url,
                "file_size": item.file_size,
            }
        }

    def _deserialize_item(self, item_data: Dict[str, Dict[str, Any]]) -> CachedItem:
        """Converts a raw dict data into a CachedItem object"""
        key_str = list(item_data.keys())[0]
        item_info = item_data[key_str]

        url, format_str, quality_str = key_str.split(DEFAULT_STRING_DIVISOR)
        key = CacheKey(
            url=url,
            format_value=Formats(format_str),
            quality=Quality(quality_str) if quality_str != 'none' else None
        )

        local_path = Path(item_info["local_path"]) if item_info.get("local_path") else None
        remote_url = item_info.get("remote_url")
        file_size = item_info.get("file_size", UNKNOWN_FILE_SIZE)

        return CachedItem(
            key=key,
            local_path=local_path,
            remote_url=remote_url,
            file_size=file_size,
        )