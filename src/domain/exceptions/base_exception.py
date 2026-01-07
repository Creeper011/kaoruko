from src.domain.enum.error_types import ErrorTypes

class ApplicationBaseException(Exception):
    """Base exception class for the application."""
    def __init__(self, *args: object, error_type: ErrorTypes = ErrorTypes.UNKNOWN) -> None:
        super().__init__(*args)
        self.error_type = error_type