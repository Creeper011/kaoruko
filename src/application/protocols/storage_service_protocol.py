from typing import Protocol
from pathlib import Path

class StorageServiceProtocol(Protocol):
    """Protocol for storage service. (Like google drive)"""
    
    async def upload(self, file_path: Path) -> str:
        """Upload a file to the storage service. Returns the file URL."""
        ...