from src.domain.enum.error_types import ErrorTypes
from src.domain.exceptions import ApplicationBaseException

class DiscordException(ApplicationBaseException):
    """Base exception for all Discord-related errors, excluding presentation errors."""
    def __init__(self, *args: object, error_type: ErrorTypes = ErrorTypes.DISCORD_ERROR) -> None:
        super().__init__(*args, error_type=error_type)

class BotException(DiscordException):
    """Raised when a general bot error occurs."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args, error_type=ErrorTypes.BOT_DISCORD_ERROR)