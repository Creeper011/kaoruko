from src.domain.exceptions import ApplicationBaseException
from src.domain.enum.error_types import ErrorTypes

class StorageError(ApplicationBaseException):
    """Base exception for all storage-related errors"""
    def __init__(self, *args: object, error_type: ErrorTypes = ErrorTypes.STORAGE_ERROR) -> None:
        super().__init__(*args, error_type=error_type)

class UploadFailed(StorageError):
    """Raised when an upload to a remote storage fails."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args, error_type=ErrorTypes.UPLOAD_FAILED)