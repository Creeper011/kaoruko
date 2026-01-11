from logging import Logger
from pathlib import Path
from typing import Optional
from src.application.protocols.download_service_protocol import DownloadServiceProtocol
from src.application.protocols.temp_service_protocol import TempServiceProtocol
from src.infrastructure.services.cache.cache_manager import CacheManager
from src.application.protocols.remote_storage_service_protocol import RemoteStorageServiceProtocol
from src.application.protocols.url_validator_protocol import URLValidatorProtocol
from src.application.dto.request.download_request import DownloadRequest
from src.application.dto.output.download_output import DownloadOutput
from src.application.models.cached_item import CachedItem
from src.application.models.cache_key import CacheKey
from src.domain.exceptions import (
    DownloadFailed,
    BlacklistException,
    UrlException,
    StorageError,
)


class DownloadUsecase():
    """Usecase for downloading files with caching and storage handling."""
    
    def __init__(self, download_service: DownloadServiceProtocol, temp_service: TempServiceProtocol,
                 cache_manager: CacheManager, storage_service: RemoteStorageServiceProtocol,
                 url_validator: URLValidatorProtocol, blacklist_sites: list[str], logger: Logger) -> None:
        self.download_service = download_service
        self.temp_service = temp_service
        self.cache_manager = cache_manager
        self.storage_service = storage_service
        self.url_validator = url_validator
        self.blacklist_sites = blacklist_sites
        self.logger = logger

        self.logger.info("DownloadUsecase initialized")

    async def execute(self, request: DownloadRequest) -> DownloadOutput:
        self._validate_request(request)

        cache_key = self._create_cache_key(request)

        cached_item = self.cache_manager.get_item(cache_key)
        if cached_item:
            output = self._handle_cache_hit(cached_item)
            if output: return output

        async with self.temp_service.create_session() as temp_folder:
            try:
                downloaded_path = await self.download_service.download(
                    request.url, request.format, temp_folder
                )
                file_size = downloaded_path.stat().st_size

                if file_size > request.file_size_limit:
                    self.logger.debug(f"File size exceeds limit {file_size} (limit: {request.file_size_limit}), uploading to remote storage")
                    return await self._handle_remote_storage(cache_key, downloaded_path, file_size)
                
                return self._handle_local_storage(cache_key, downloaded_path)

            except Exception as e:
                self.logger.error(f"Execution failed: {e}")
                raise DownloadFailed(f"Failed to process download: {e}")
            
    def _create_cache_key(self, request: DownloadRequest) -> CacheKey:
        if request.format.is_audio():
            self.logger.debug("Creating cache key for audio format without quality")
            return CacheKey(
                url=request.url,
                format_value=request.format,
                quality=None,
            )
        
        return CacheKey(
            url=request.url,
            format_value=request.format,
            quality=request.quality,
        )

    def _validate_request(self, request: DownloadRequest):
        if not self.url_validator.is_valid(request.url):
            raise UrlException(f"Invalid URL: {request.url}")
        if request.url in self.blacklist_sites:
            raise BlacklistException("URL is blacklisted")

    def _handle_cache_hit(self, item: CachedItem) -> Optional[DownloadOutput]:
        if item.remote_url:
            return DownloadOutput(file_path=None, file_url=item.remote_url, file_size=item.file_size)
        
        if item.local_path and item.local_path.exists():
            return DownloadOutput(file_path=item.local_path, file_url=None, file_size=item.file_size)
        
        return None

    async def _handle_remote_storage(self, key: CacheKey, path: Path, size: int) -> DownloadOutput:
        final_url = await self.storage_service.upload(path)
        cached = self.cache_manager.store_item(key=key, source_file=None, remote_url=final_url)
        return DownloadOutput(file_path=None, file_url=cached.remote_url, file_size=size)

    def _handle_local_storage(self, key: CacheKey, path: Path) -> DownloadOutput:
        cached = self.cache_manager.store_item(key=key, source_file=path, remote_url=None)
        return DownloadOutput(file_path=cached.local_path, file_url=None, file_size=cached.file_size)