from abc import ABC, abstractmethod
from typing import Any

class DownloaderPort(ABC):
    @abstractmethod
    async def __aenter__(self) -> Any:
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    @abstractmethod
    def get_filepath(self) -> str:
        ...

    @abstractmethod
    def cancel_download(self) -> None:
        ...
    
    @abstractmethod
    def _cleanup(self) -> None:
        ...
