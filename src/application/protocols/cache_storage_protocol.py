from typing import Protocol, Dict, Any
from pathlib import Path

class CacheStorageProtocol(Protocol):
    """Protocol defining storage operations for cache persistence."""
    
    async def load_index(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads the complete cache index from storage.
        
        Returns:
            Dictionary mapping cache keys to their metadata entries.
        """
        ...
    
    async def save_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        """
        Persists the complete cache index to storage.
        
        Args:
            index: Dictionary containing all cache entries and their metadata.
        """
        ...
    
    def store_file(self, key: str, source_path: Path, destination_name: str) -> Path:
        """
        Stores a file in the cache storage system.
        
        Args:
            key: Cache key identifying this entry.
            source_path: Path to the source file to be stored.
            destination_name: Desired filename in cache storage.
            
        Returns:
            Path where the file was stored.
        """
        ...
    
    def file_exists(self, path: Path) -> bool:
        """
        Checks if a file exists in the storage system.
        
        Args:
            path: Path to check for existence.
            
        Returns:
            True if file exists, False otherwise.
        """
        ...
    
    def get_file_size(self, path: Path) -> int:
        """
        Retrieves the size of a stored file.
        
        Args:
            path: Path to the file.
            
        Returns:
            File size in bytes.
        """
        ...
    
    def delete_file(self, path: Path) -> None:
        """
        Removes a file from the storage system.
        
        Args:
            path: Path to the file to be deleted.
        """
        ...
    
    def cleanup_orphaned_files(self, valid_paths: set[Path]) -> int:
        """
        Removes files that are no longer referenced in the cache index.
        
        Args:
            valid_paths: Set of paths that should be preserved.
            
        Returns:
            Number of orphaned files removed.
        """
        ...

    async def move_file_to_cache(self, key: str, source_path: Path) -> Path:
        """Moves a file to the cache storage structure.
        Args:
            key: Cache key identifying this entry.
            source_path: Path to the source file to be moved.
        Returns:
            Path where the file was moved in cache storage.
        """