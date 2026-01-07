import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional
from logging import Logger

from src.application.models.cached_item import CachedItem
from src.core.constants import CACHE_DIR, CACHE_INDEX_FILE

class CacheService():
    """Cache service responsible for managing local and remote cache persistence."""

    def __init__(self, logger: Logger, cache_dir: Optional[Path] = CACHE_DIR, index_file: Optional[Path] = CACHE_INDEX_FILE) -> None:
        self.logger = logger
        self.cache_dir = cache_dir
        self.index_file = index_file
        self.cache_index: Dict[str, dict] = {}

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_index()

        self.logger.info(f"CacheService initialized at: {self.cache_dir}")

    def _load_index(self) -> None:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    self.cache_index = json.load(f)
                self.logger.debug(f"Loaded {len(self.cache_index)} cache entries")
            except Exception as e:
                self.logger.warning(f"Failed to load cache index: {e}")
                self.cache_index = {}

    def _save_index(self) -> None:
        try:
            with open(self.index_file, "w") as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cache index: {e}")

    def get(self, key: str) -> CachedItem | None:
        if key not in self.cache_index:
            self.logger.debug(f"Cache MISS for key: {key}")
            return None

        entry = self.cache_index[key]
        local_path = Path(entry["local_path"]) if entry.get("local_path") else None

        if local_path and not local_path.exists():
            self.logger.warning(f"Cached file missing: {local_path}")
            self._invalidate(key)
            return None

        return CachedItem(
            local_path=local_path,
            remote_url=entry.get("remote_url"),
            file_size=entry.get("file_size"),
        )

    def store(self, key: str, source_path: Path, file_size: int | None = None, remote_url: str | None = None) -> CachedItem:
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if file_size is None:
            file_size = source_path.stat().st_size

        cache_dir = self._get_cache_dir(key)
        persistent_path = cache_dir / source_path.name

        shutil.copy2(source_path, persistent_path)

        self.cache_index[key] = {
            "local_path": str(persistent_path),
            "remote_url": remote_url,
            "file_size": file_size,
        }

        self._save_index()

        self.logger.debug(f"Cached local file: {persistent_path}")

        return CachedItem(
            local_path=persistent_path,
            remote_url=remote_url,
            file_size=file_size,
        )

    def register_remote(self, key: str, remote_url: str, file_size: int | None = None) -> CachedItem:
        self.cache_index[key] = {
            "local_path": None,
            "remote_url": remote_url,
            "file_size": file_size,
        }

        self._save_index()

        self.logger.debug(f"Cached remote URL for key: {key}")

        return CachedItem(
            local_path=None,
            remote_url=remote_url,
            file_size=file_size,
        )

    def _get_cache_dir(self, key: str) -> Path:
        cache_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        cache_path = self.cache_dir / cache_id
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path

    def _invalidate(self, key: str) -> None:
        self.cache_index.pop(key, None)
        self._save_index()
        self.logger.debug(f"Invalidated cache entry for key: {key}")
