from typing import Protocol, AsyncGenerator
from pathlib import Path
from contextlib import asynccontextmanager

class TempServiceProtocol(Protocol):
    """Protocol for temporary file service."""

    @asynccontextmanager
    async def create_session(self) -> AsyncGenerator[Path, None]:
        """Create a temporary folder session that cleans up itself."""
        ...
        yield Path()