from typing import Optional
from src.domain.interfaces.dto.output.download_output import DownloadOutput
from src.domain.interfaces.dto.request.download_request import DownloadRequest
from src.domain.interfaces.protocols.download_protocol import DownloadProtocol
from src.domain.exceptions import InvalidDownloadRequest

class DownloadUsecase:
    """
    Use case responsible for orchestrating the download of media files.
    """

    def __init__(self, service: DownloadProtocol):
        self.service = service

    def _validate(self, request: DownloadRequest) -> bool:
        """Validate input."""
        # TODO: Implement validation logic
        return True

    async def execute(self, request: DownloadRequest) -> DownloadOutput:
        """
        Executes the download process.

        Args:
            request (DownloadRequest): Contains URL, format, quality, etc.

        Returns:
            DownloadOutput: The result of the download, including file path and metadata.

        Raises:
            InvalidDownloadRequest: If the request is invalid (validation not yet implemented).
        """
        if not self._validate(request):
            raise InvalidDownloadRequest()

        async with self.service(request.url, request.format, request.quality) as service:
            output = await service.get_response()

        return output
