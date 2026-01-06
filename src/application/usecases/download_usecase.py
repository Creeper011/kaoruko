from src.application.protocols.download_service_protocol import DownloadServiceProtocol
from src.application.protocols.temp_service_protocol import TempServiceProtocol
from src.application.protocols.cache_service_protocol import CacheServiceProtocol
from src.application.protocols.storage_service_protocol import StorageServiceProtocol
from src.application.dto.request.download_request import DownloadRequest
from src.application.dto.output.download_output import DownloadOutput
from src.domain.exceptions.download_exceptions import DownloadFailed
from src.domain.exceptions.storage_exceptions import StorageError

class DownloadUsecase():
    def __init__(self, download_service: DownloadServiceProtocol, temp_service: TempServiceProtocol, cache_service: CacheServiceProtocol, storage_service: StorageServiceProtocol):
        self.download_service = download_service
        self.temp_service = temp_service
        self.cache_service = cache_service
        self.storage_service = storage_service

    async def execute(self, request: DownloadRequest) -> DownloadOutput:
        cached_item = self.cache_service.get(request.url)
        
        if cached_item:
            if cached_item.remote_url:
                return DownloadOutput(
                    file_path=None, 
                    file_url=cached_item.remote_url,
                    file_size=None
                )
            
            if cached_item.local_path and cached_item.local_path.exists():
                return DownloadOutput(
                    file_path=cached_item.local_path,
                    file_url=None,
                    file_size=cached_item.local_path.stat().st_size
                )

        async with self.temp_service.create_session() as temp_folder:
            try:
                downloaded_file_path = await self.download_service.download(request.url, temp_folder)
            except Exception as error:
                raise DownloadFailed(f"Failed to download from {request.url}") from error

            file_size = downloaded_file_path.stat().st_size

            if file_size > request.file_size_limit:
                try:
                    final_url = await self.storage_service.upload(downloaded_file_path)
                    
                    self.cache_service.set(
                        key=request.url,
                        file_path=None,
                        remote_url=final_url
                    )

                    return DownloadOutput(
                        file_path=None,
                        file_url=final_url,
                        file_size=file_size
                    )
                except Exception as error:
                    raise StorageError(f"Failed to upload file to storage") from error
            
            else:
                persistent_path = await self.cache_service.save_local_file(downloaded_file_path)
                
                self.cache_service.set(
                    key=request.url,
                    file_path=persistent_path,
                    remote_url=None
                )

                return DownloadOutput(
                    file_path=persistent_path,
                    file_url=None,
                    file_size=file_size
                )