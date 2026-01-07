import datetime
from discord import Embed
from src.domain.enum.error_types import ErrorTypes
from src.domain.exceptions import ApplicationBaseException

EMBED_COLOR = 0xFF0000 

class ErrorEmbedFactory():
    """Factory to create error embeds for Discord."""
    
    @staticmethod
    def create_error_embed(error: ApplicationBaseException) -> Embed:
        """Create a Discord embed for the given error."""

        error_type = ErrorEmbedFactory._get_error_type(error)
        description = str(error) if str(error) else "An unknown error occurred."

        embed = Embed(
            description=f"# Kaoruko panic!\n{description}",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            color=EMBED_COLOR,
        )
        embed.add_field(name="Error Type", value=error_type.value)
        return embed
    
    @staticmethod
    def _get_error_type(error: ApplicationBaseException) -> ErrorTypes:
        """Get the error type based on the exception."""
        if hasattr(error, 'error_type'):
            return error.error_type
        
        return ErrorTypes.UNKNOWN