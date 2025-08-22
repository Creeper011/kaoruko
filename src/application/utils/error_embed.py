import discord
from typing import Optional
from src.application.constants.error_types import ErrorTypes

def create_error(error: str, code: Optional[str] = None, type: Optional[ErrorTypes] = None,
                  color: Optional[int] = None, note: Optional[str] = None) -> discord.Embed:
    """Create an error embed for Discord messages.
    Args:
        error (str): The error message to display.
        code (Optional[str]): Optional error code.
        type (Optional[ErrorTypes]): Optional error type.
        color (Optional[int]): Optional color for the embed.
        note (Optional[str]): Additional note to include in the embed.
    Returns:
        discord.Embed: The constructed error embed.
    """
    note_text = f"\nNote: *{note}*" if note else ""
    type_text = f"\nType: {type.value}" if type else ""
    code_text = f"\n```{code}```" if code else ""

    embed = discord.Embed(
        title="⛔ Error:",
        description=f"Error: {error}{type_text}{note_text}{code_text}",
        colour=color if color else 0xd54e44
    )
    return embed