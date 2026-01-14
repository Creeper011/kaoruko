from abc import ABC, abstractmethod
from src.application.dto.request.download_request import DownloadRequest
from src.application.models.dataclasses.download_storage_decision import DownloadStorageDecision
from src.domain.models import DownloadedFile


class StorageDecisionStrategy(ABC):
    """Abstract base class for storage decision strategies."""

    @abstractmethod
    async def decide(self, request: DownloadRequest, downloaded_file: DownloadedFile) -> DownloadStorageDecision:
        pass


class SizeBasedStorageDecisionStrategy(StorageDecisionStrategy):
    """Storage decision strategy based on file size."""

    async def decide(self, request: DownloadRequest, downloaded_file: DownloadedFile) -> DownloadStorageDecision:
        from src.domain.enum.download_destination import DownloadDestination
        if downloaded_file.file_size > request.file_size_limit:
            return DownloadStorageDecision(destination=DownloadDestination.REMOTE)
        else:
            return DownloadStorageDecision(destination=DownloadDestination.LOCAL)