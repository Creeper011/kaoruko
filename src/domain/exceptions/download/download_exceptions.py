
class MediaFilepathNotFound(Exception):
    """Raised when the downloaded media file is not found."""
    pass

class InvalidDownloadRequest(Exception):
    """Raised when the download request is invalid."""
    pass