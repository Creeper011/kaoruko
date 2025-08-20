class InvalidUrl(Exception):
    """Raised when the provided URL is invalid."""
    pass

class InvalidFormat(Exception):
    """Raised when the provided format is invalid."""
    pass

class InvalidSpeed(Exception):
    """Raised when the provided speed is invalid."""
    pass

class GenericError(Exception):
    """A generic exception for unspecified errors."""
    pass

class InvalidSpeedValue(Exception):
    """Raised when the speed value is out of allowed range."""
    pass

class InvalidPreservePitchValue(Exception):
    """Raised when the 'preserve pitch' value is invalid."""
    pass

class MediaFilepathNotFound(Exception):
    """Raised when the media file path cannot be found."""
    pass

class FailedToUploadDrive(Exception):
    """Raised when the upload to Google Drive fails."""
    pass