
class GenericError(Exception):
    """Base class for generic errors that do not fit into specific categories."""
    pass

class FailedToUploadDrive(Exception):
    """Raised when a file fails to upload to a drive (e.g., Google Drive or similar)."""
    pass

class InvalidFileType(Exception):
    """Raised when an unsupported or invalid file type is encountered."""
    pass
