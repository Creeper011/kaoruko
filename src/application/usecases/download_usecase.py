from logging import Logger
from src.application.protocols.download_service_protocol import DownloadServiceProtocol
from src.application.protocols.temp_service_protocol import TempServiceProtocol
from src.application.protocols.cache_service_protocol import CacheServiceProtocol
from src.application.protocols.storage_service_protocol import StorageServiceProtocol
from src.application.protocols.url_validator_protocol import URLValidatorProtocol
from src.application.dto.request.download_request import DownloadRequest
from src.application.dto.output.download_output import DownloadOutput
from src.domain.exceptions import (
    DownloadFailed,
    BlacklistException,
    UrlException,
    StorageError,
)


class DownloadUsecase():
    """Usecase for downloading files with caching and storage handling."""
    
    def __init__(self, download_service: DownloadServiceProtocol, temp_service: TempServiceProtocol,
                 cache_service: CacheServiceProtocol, storage_service: StorageServiceProtocol,
                 url_validator: URLValidatorProtocol, blacklist_sites: list[str], logger: Logger) -> None:
        self.download_service = download_service
        self.temp_service = temp_service
        self.cache_service = cache_service
        self.storage_service = storage_service
        self.url_validator = url_validator
        self.blacklist_sites = blacklist_sites
        self.logger = logger

        self.logger.info("DownloadUsecase initialized")

    async def execute(self, request: DownloadRequest) -> DownloadOutput:
        self.logger.info(f"Starting download execution for URL: {request.url}")
        self.logger.debug(
            f"File size limit: {request.file_size_limit} bytes "
            f"({request.file_size_limit / 1024 / 1024:.2f} MB)"
        )

        self.logger.debug("Checking URL validity...")
        if not self.url_validator.is_valid(request.url):
            self.logger.warning(f"Invalid URL provided: {request.url}")
            raise UrlException(f"Invalid URL: {request.url}")

        if request.url in self.blacklist_sites:
            self.logger.warning(f"URL is blacklisted: {request.url}")
            raise BlacklistException(f"URL is blacklisted: {request.url}")
        
        self.logger.debug("Checking cache for existing download...")
        cached_item = self.cache_service.get(request.url)

        if cached_item:
            self.logger.info(f"Cache HIT for URL: {request.url}")

            if cached_item.remote_url:
                self.logger.debug(f"Returning cached remote URL: {cached_item.remote_url}")
                return DownloadOutput(
                    file_path=None,
                    file_url=cached_item.remote_url,
                    file_size=cached_item.file_size,
                )

            if cached_item.local_path and cached_item.local_path.exists():
                self.logger.debug(f"Returning cached local file: {cached_item.local_path}")
                return DownloadOutput(
                    file_path=cached_item.local_path,
                    file_url=None,
                    file_size=cached_item.file_size or cached_item.local_path.stat().st_size,
                )

            self.logger.warning(
                f"Cached local file not found at path: {cached_item.local_path}. Proceeding to re-download."
            )

        async with self.temp_service.create_session() as temp_folder:
            self.logger.debug(f"Created temporary session at: {temp_folder}")

            try:
                self.logger.info(f"Initiating download from: {request.url}")
                downloaded_file_path = await self.download_service.download(request.url, request.format, temp_folder)
                self.logger.info(f"Download completed: {downloaded_file_path.name}")

            except Exception as error:
                self.logger.error(f"Download failed for URL: {request.url} - {error}", exc_info=True)
                raise DownloadFailed(f"Failed to download from {request.url}") from error

            file_size = downloaded_file_path.stat().st_size
            self.logger.debug(
                f"Downloaded file size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)"
            )

            if file_size > request.file_size_limit:
                self.logger.info(
                    f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds limit "
                    f"({request.file_size_limit / 1024 / 1024:.2f} MB) - uploading to remote storage"
                )

                try:
                    self.logger.debug("Uploading file to remote storage...")
                    final_url = await self.storage_service.upload(downloaded_file_path)
                    self.logger.info(f"File uploaded successfully to: {final_url}")

                    self.logger.debug("Registering remote URL in cache for future requests")
                    
                    cached_item = self.cache_service.register_remote(
                        key=request.url,
                        remote_url=final_url,
                        file_size=file_size,
                    )

                    return DownloadOutput(
                        file_path=None,
                        file_url=cached_item.remote_url,
                        file_size=cached_item.file_size,
                    )
                except Exception as error:
                    self.logger.error(f"Storage upload failed: {error}", exc_info=True)
                    raise StorageError(f"Failed to upload file to storage") from error

            else:
                self.logger.info(
                    f"File size ({file_size / 1024 / 1024:.2f} MB) within limit "
                    f"({request.file_size_limit / 1024 / 1024:.2f} MB) - saving locally"
                )
                self.logger.debug("Asking CacheService to persist the file from temp to .cache...")

                cached_item = self.cache_service.store(
                    key=request.url,
                    source_path=downloaded_file_path,
                    file_size=file_size,
                )

                self.logger.info(f"File saved to persistent storage (.cache): {cached_item.local_path}")
                return DownloadOutput(
                    file_path=cached_item.local_path,
                    file_url=None,
                    file_size=cached_item.file_size,
                )
