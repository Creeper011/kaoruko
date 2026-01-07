from src.domain.exceptions import ApplicationBaseException
from src.domain.enum.error_types import ErrorTypes

class BlacklistException(ApplicationBaseException):
    """Base exception for all blacklist-related errors"""
    def __init__(self, *args: object, error_type: ErrorTypes = ErrorTypes.BLACKLISTED_SEARCH) -> None:
        super().__init__(*args, error_type=error_type)