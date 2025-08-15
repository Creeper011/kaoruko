from src.domain.ports.downloader_port import DownloaderPort
from src.infrastructure.services.downloader import Downloader
from typing import Any

class DownloaderAdapter(DownloaderPort):
    def __init__(self, url: str, format: str):
        self._downloader = Downloader(url, format)

    async def __aenter__(self) -> Any:
        return await self._downloader.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._downloader.__aexit__(exc_type, exc_val, exc_tb)

    def get_filepath(self) -> str:
        return self._downloader.get_filepath()

    def cancel_download(self) -> None:
        self._downloader.cancel_download()

    def _cleanup(self) -> None:
        self._downloader._cleanup()
