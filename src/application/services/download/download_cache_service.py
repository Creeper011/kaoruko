from typing import Optional
from src.application.services import CacheManager
from src.application.protocols.remote_storage_service_protocol import RemoteStorageServiceProtocol
from src.application.dto.request.download_request import DownloadRequest
from src.application.dto.output.download_output import DownloadOutput
from src.application.models.dataclasses.cached_item import CachedItem
from src.application.models.dataclasses.cache_key import CacheKey
from src.domain.enum.download_destination import DownloadDestination
from src.domain.models import DownloadedFile


class DownloadCacheService():
    """Service for handling download caching logic."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    def create_cache_key(self, request: DownloadRequest) -> CacheKey:
        if request.format.is_audio():
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

    async def get_cached_output(self, request: DownloadRequest) -> Optional[DownloadOutput]:
        cache_key = self.create_cache_key(request)
        cached_item = await self.cache_manager.get_item(cache_key)
        if cached_item:
            if cached_item.remote_url:
                return DownloadOutput(file_path=None, file_url=cached_item.remote_url, file_size=cached_item.file_size)
            if cached_item.local_path:
                return DownloadOutput(file_path=cached_item.local_path, file_url=None, file_size=cached_item.file_size)
        return None

    async def store_download(self, cache_key: CacheKey, downloaded_file: DownloadedFile, destination: DownloadDestination, storage_service: RemoteStorageServiceProtocol) -> DownloadOutput:
        if destination == DownloadDestination.REMOTE:
            final_url = await storage_service.upload(downloaded_file.file_path)
            cached = await self.cache_manager.store_item(key=cache_key, source_file=None, remote_url=final_url, file_size=downloaded_file.file_size)
            return DownloadOutput(file_path=None, file_url=cached.remote_url, file_size=downloaded_file.file_size)
        else:
            cached = await self.cache_manager.store_item(key=cache_key, source_file=downloaded_file.file_path, remote_url=None, file_size=downloaded_file.file_size)
            return DownloadOutput(file_path=cached.local_path, file_url=None, file_size=cached.file_size)