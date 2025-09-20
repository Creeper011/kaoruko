from typing import Optional, Protocol, runtime_checkable
from src.domain.interfaces.dto.output.extract_audio_output import ExtractAudioOutput

@runtime_checkable
class ExtractAudioProtocol(Protocol):
    def __init__(self, url: str):
        ...
        
    async def __aenter__(self) -> "ExtractAudioProtocol":
        ...

    async def __aexit__(self, exc_type, exc_val, tb) -> None:
        ...

    async def get_response(self) -> ExtractAudioOutput:
        """Fetches the extract audio response and returns a ExtractAudioOutput object."""
        ...