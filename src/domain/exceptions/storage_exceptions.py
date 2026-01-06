class StorageError(Exception):
    """Base exception for all storage-related errors"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UploadFailed(StorageError):
    """Raised when an upload to a remote storage fails."""