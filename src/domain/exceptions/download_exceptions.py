from src.domain.enum.error_types import ErrorTypes
from src.domain.exceptions import ApplicationBaseException

class DownloadError(ApplicationBaseException):
    """Base exception for all download-related errors"""
    def __init__(self, *args: object, error_type: ErrorTypes = ErrorTypes.DOWNLOAD_ERROR) -> None:
        super().__init__(*args, error_type=error_type)

class DownloadFailed(DownloadError):
    """Raised when a download fails for any reason."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args, error_type=ErrorTypes.DOWNLOAD_FAILED)
