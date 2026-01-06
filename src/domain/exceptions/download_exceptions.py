
class DownloadError(Exception):
    """Base exception for all download-related errors"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class DownloadFailed(DownloadError):
    """Raised when a download fails for any reason."""
