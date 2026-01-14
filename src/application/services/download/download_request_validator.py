from src.application.protocols.url_validator_protocol import URLValidatorProtocol
from src.application.dto.request.download_request import DownloadRequest
from src.domain.exceptions import UrlException, BlacklistException

class DownloadRequestValidator():
    """Validates download requests for URL validity and blacklist status."""

    def __init__(self, url_validator: URLValidatorProtocol, blacklist_sites: list[str]) -> None:
        self.url_validator = url_validator
        self.blacklist_sites = blacklist_sites

    def validate(self, request: DownloadRequest) -> None:
        """
        Validates the given download request.

        Args:
            request: The DownloadRequest object to validate.

        Raises:
            UrlException: If the URL is invalid.
            BlacklistException: If the URL is blacklisted.
        """
        if not self.url_validator.is_valid(request.url):
            raise UrlException(f"Invalid URL: {request.url}")
        
        for site in self.blacklist_sites:
            if site in request.url:
                raise BlacklistException(f"URL is blacklisted: {request.url}")