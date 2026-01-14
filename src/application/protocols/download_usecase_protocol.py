from typing import Protocol, runtime_checkable
from src.application.dto.output.download_output import DownloadOutput
from src.application.dto.request.download_request import DownloadRequest

@runtime_checkable
class DownloadUseCaseProtocol(Protocol):
    async def execute(self, request: DownloadRequest) -> DownloadOutput:
        ...