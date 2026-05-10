from pathlib import Path

import pytest

from src.application.dto.request.download_request import DownloadRequest
from src.application.usecases.download_usecase import DownloadUsecase
from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality
from src.domain.models.download_file import DownloadedFile
from src.domain.models.settings.download_settings import DownloadSettings


class FakeDownloaderService:
    def __init__(self, payload: bytes = b"demo", filename: str = "demo.mp4") -> None:
        self.payload = payload
        self.filename = filename

    async def download(self, request, output_path: Path, progress_callback=None) -> DownloadedFile:
        if progress_callback is not None:
            await progress_callback(37.5)

        file_path = output_path / self.filename
        file_path.write_bytes(self.payload)
        return DownloadedFile(file_path=file_path, file_size=len(self.payload))


class FakeStorageService:
    async def upload(self, file_path: Path) -> str:
        return f"https://drive.example/{file_path.name}"


class FakeTempService:
    class _Session:
        def __init__(self, path: Path) -> None:
            self.path = path

        async def __aenter__(self) -> Path:
            self.path.mkdir(parents=True, exist_ok=True)
            return self.path

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    def __init__(self, path: Path) -> None:
        self.path = path

    def create_session(self):
        return self._Session(self.path)


def _build_request(file_size_limit: int = 25 * 1024 * 1024) -> DownloadRequest:
    return DownloadRequest(
        url="https://example.com/video",
        file_size_limit=file_size_limit,
        format=Formats.MP4,
        quality=Quality._720,
    )


@pytest.mark.asyncio
async def test_download_usecase_returns_local_bytes_and_progress(tmp_path) -> None:
    progress_updates: list[float] = []
    usecase = DownloadUsecase(
        downloader_service=FakeDownloaderService(payload=b"video-bytes"),
        storage_service=FakeStorageService(),
        temp_service=FakeTempService(tmp_path / "session"),
        settings=DownloadSettings(file_size_limit=25 * 1024 * 1024),
        logger=__import__("logging").getLogger("test"),
    )

    result = await usecase.execute(
        _build_request(),
        progress_callback=lambda value: _collect_progress(progress_updates, value),
    )

    assert result.file_bytes == b"video-bytes"
    assert result.file_name == "demo.mp4"
    assert result.file_url is None
    assert progress_updates == [37.5]


@pytest.mark.asyncio
async def test_download_usecase_returns_remote_url(tmp_path) -> None:
    usecase = DownloadUsecase(
        downloader_service=FakeDownloaderService(payload=b"video-bytes"),
        storage_service=FakeStorageService(),
        temp_service=FakeTempService(tmp_path / "session"),
        settings=DownloadSettings(file_size_limit=1),
        logger=__import__("logging").getLogger("test"),
    )

    result = await usecase.execute(_build_request(file_size_limit=1))

    assert result.file_url == "https://drive.example/demo.mp4"
    assert result.file_name == "demo.mp4"
    assert result.file_bytes is None


async def _collect_progress(progress_updates: list[float], value: float) -> None:
    progress_updates.append(value)
