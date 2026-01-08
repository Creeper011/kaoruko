import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any
from logging import Logger

from src.core.constants import CACHE_DIR, CACHE_INDEX_FILE


class JSONCacheStorage():
    """Concrete implementation of cache storage using JSON."""
    
    def __init__(self, logger: Logger, cache_dir: Path = CACHE_DIR, 
                 index_file: Path = CACHE_INDEX_FILE) -> None:
        self.logger = logger
        self.cache_dir = cache_dir
        self.index_file = index_file
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"FilesystemCacheStorage initialized at: {self.cache_dir}")
    
    def load_index(self) -> Dict[str, Dict[str, Any]]:
        """Loads cache index from JSON file."""
        if not self.index_file.exists():
            self.logger.debug("Cache index file does not exist, returning empty index")
            return {}
        
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.logger.debug(f"Loaded cache index with {len(data)} entries")
            return data
        except Exception as error:
            self.logger.warning(f"Failed to load cache index: {error}")
            return {}
    
    def save_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        """Saves cache index to JSON file."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Saved cache index with {len(index)} entries")
        except Exception as error:
            self.logger.error(f"Failed to save cache index: {error}")
    
    def store_file(self, key: str, source_path: Path, destination_name: str) -> Path:
        """Stores a file in the cache directory structure."""
        cache_subdir = self._get_cache_dir(key)
        destination_path = cache_subdir / destination_name
        
        shutil.copy2(source_path, destination_path)
        self.logger.debug(f"Stored file at: {destination_path}")
        
        return destination_path
    
    def file_exists(self, path: Path) -> bool:
        """Checks if a file exists in the filesystem."""
        return path.exists() and path.is_file()
    
    def get_file_size(self, path: Path) -> int:
        """Gets the size of a file in bytes."""
        return path.stat().st_size
    
    def delete_file(self, path: Path) -> None:
        """Deletes a file from the filesystem."""
        try:
            if path.exists():
                path.unlink()
                self.logger.debug(f"Deleted file: {path}")
        except Exception as error:
            self.logger.warning(f"Failed to delete file {path}: {error}")
    
    def cleanup_orphaned_files(self, valid_paths: set[Path]) -> int:
        """Removes files not referenced in the cache index."""
        removed_count = 0
        
        for subdir in self.cache_dir.iterdir():
            if not subdir.is_dir():
                continue
            
            for file_path in subdir.iterdir():
                if file_path not in valid_paths:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        self.logger.debug(f"Removed orphaned file: {file_path}")
                    except Exception as error:
                        self.logger.warning(f"Failed to remove orphaned file {file_path}: {error}")
        
        return removed_count
    
    def _get_cache_dir(self, key: str) -> Path:
        """Generates a cache subdirectory based on key hash."""
        cache_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        cache_path = self.cache_dir / cache_id
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path
    
    def move_file_to_cache(self, key: str, source_path: Path) -> Path:
        """Moves a file to the cache storage structure."""
        cache_subdir = self._get_cache_dir(key)
        destination_path = cache_subdir / source_path.name
        
        shutil.move(str(source_path), str(destination_path))
        self.logger.debug(f"Moved file to cache at: {destination_path}")
        
        return destination_path