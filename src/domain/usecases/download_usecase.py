from typing import Optional, Set
import validators
from urllib.parse import urlparse
from src.domain.interfaces.dto.output.download_output import DownloadOutput
from src.domain.interfaces.dto.request.download_request import DownloadRequest
from src.domain.interfaces.protocols.download_protocol import DownloadProtocol
from src.domain.exceptions import InvalidDownloadRequest, BlacklistedSiteError


class DownloadUsecase:
    """
    Use case responsible for orchestrating the download of media files.
    """

    def __init__(self, service: DownloadProtocol, blacklist: Set[str]):
        """Initializes the use case with the download service and the blacklist."""
        self.service = service
        self.blacklist = blacklist

    def _validate(self, request: DownloadRequest) -> bool:
        """Validate input and modify URL if needed."""
        if not request.url or not request.url.strip():
            raise InvalidDownloadRequest("URL cannot be empty")

        if validators.url(request.url):
            domain = urlparse(request.url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]

            if domain in self.blacklist:
                raise BlacklistedSiteError(f"Domain '{domain}' is blacklisted.")
        else:
            request.url = f"ytsearch:{request.url}"

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

        async with self.service(request.url, request.format, request.quality, request.file_limit,
                                request.should_transcode, request.verbose, request.fetch_metadata) as service:
            output = await service.get_response()

        return output
