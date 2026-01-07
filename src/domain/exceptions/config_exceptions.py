from src.domain.enum.error_types import ErrorTypes
from src.domain.exceptions import ApplicationBaseException

class ConfigError(ApplicationBaseException):
    """Base exception for all config-related errors"""
    def __init__(self, *args: object, error_type: ErrorTypes = ErrorTypes.UNKNOWN) -> None:
        super().__init__(*args, error_type=error_type)

class YamlFailedLoad(ConfigError):
    """Raised when loading configuration from a YAML file fails."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args, error_type=ErrorTypes.LOADER_ERROR)

class EnvFailedLoad(ConfigError):
    """Raised when loading configuration from environment variables fails."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args, error_type=ErrorTypes.LOADER_ERROR)