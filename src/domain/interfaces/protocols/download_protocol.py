from typing import Optional, Protocol, runtime_checkable
from src.domain.interfaces.dto.output.download_output import DownloadOutput

@runtime_checkable
class DownloadProtocol(Protocol):
    def __init__(self, url: str, format: str, quality: Optional[str] = None, 
                 min_size_for_drive_upload: Optional[int] = None, should_transcode: bool = False):
        ...
        
    async def __aenter__(self) -> "DownloadProtocol":
        ...

    async def __aexit__(self, exc_type, exc_val, tb) -> None:
        ...

    async def get_response(self) -> DownloadOutput:
        """Fetches the download response and returns a DownloadOutput object."""
        ...