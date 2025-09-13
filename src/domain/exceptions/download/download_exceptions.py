
class MediaFilepathNotFound(Exception):
    """Raised when the downloaded media file is not found."""
    pass

class InvalidDownloadRequest(Exception):
    """Raised when the download request is invalid."""
    pass

class DownloadFailed(Exception):
    """Raised when the download process fails."""
    pass

class UnsupportedFormat(Exception):
    """Raised when the requested format is not supported."""
    pass

class FileTooLarge(Exception):
    """Raised when the file exceeds size limits."""
    pass

class NetworkError(Exception):
    """Raised when there's a network-related error."""
    pass

class DriveUploadFailed(Exception):
    """Raised when Google Drive upload fails."""
    pass