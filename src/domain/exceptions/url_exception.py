from src.domain.exceptions import ApplicationBaseException
from src.domain.enum.error_types import ErrorTypes

class UrlException(ApplicationBaseException):
    """Base exception for all URL-related errors"""
    def __init__(self, *args: object, error_type: ErrorTypes = ErrorTypes.INVALID_URL) -> None:
        super().__init__(*args, error_type=error_type)