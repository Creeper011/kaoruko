from typing import Any

import pytest
from aiohttp import web

from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality
from src.domain.exceptions.download_exceptions import DownloadFailed
from src.services.yumeapi import YumeApiDownloadService


async def _start_test_server(app: web.Application, port: int) -> web.AppRunner:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    return runner


@pytest.mark.asyncio
async def test_yumeapi_download_service_downloads_file(tmp_path, unused_tcp_port: int) -> None:
    state: dict[str, Any] = {
        "status_calls": 0,
        "request_payload": None,
    }

    async def create_download(request: web.Request) -> web.Response:
        state["request_payload"] = await request.json()
        return web.json_response({"id": "job-1"})

    async def get_status(_: web.Request) -> web.Response:
        state["status_calls"] += 1
        if state["status_calls"] == 1:
            return web.json_response(
                {"id": "job-1", "status": "running", "progress": 50.0, "filename": "", "error": ""}
            )
        return web.json_response(
            {"id": "job-1", "status": "completed", "progress": 100.0, "filename": "video.mp4", "error": ""}
        )

    async def get_file(_: web.Request) -> web.Response:
        return web.Response(
            body=b"video-bytes",
            headers={"Content-Disposition": 'attachment; filename="video.mp4"'},
        )

    app = web.Application()
    app.router.add_post("/download", create_download)
    app.router.add_get("/download/job-1", get_status)
    app.router.add_get("/download/job-1/file", get_file)

    runner = await _start_test_server(app, unused_tcp_port)

    try:
        service = YumeApiDownloadService(
            base_url=f"http://127.0.0.1:{unused_tcp_port}",
            status_poll_interval_seconds=0.01,
            job_timeout_seconds=1.0,
        )

        result = await service.download(
            url="https://example.com/video",
            format_value=Formats.MP4,
            quality=Quality._720,
            output_folder=tmp_path,
        )
    finally:
        await runner.cleanup()

    assert state["request_payload"] == {
        "url": "https://example.com/video",
        "format": "mp4",
        "quality": "720p",
    }
    assert result.file_size == len(b"video-bytes")
    assert result.file_path.name == "video.mp4"
    assert result.file_path.read_bytes() == b"video-bytes"


@pytest.mark.asyncio
async def test_yumeapi_download_service_raises_api_failure(tmp_path, unused_tcp_port: int) -> None:
    async def create_download(_: web.Request) -> web.Response:
        return web.json_response({"id": "job-2"})

    async def get_status(_: web.Request) -> web.Response:
        return web.json_response(
            {"id": "job-2", "status": "failed", "progress": 0.0, "filename": "", "error": "boom"}
        )

    app = web.Application()
    app.router.add_post("/download", create_download)
    app.router.add_get("/download/job-2", get_status)

    runner = await _start_test_server(app, unused_tcp_port)

    try:
        service = YumeApiDownloadService(
            base_url=f"http://127.0.0.1:{unused_tcp_port}",
            status_poll_interval_seconds=0.01,
            job_timeout_seconds=1.0,
        )

        with pytest.raises(DownloadFailed, match="boom"):
            await service.download(
                url="https://example.com/video",
                format_value=Formats.MP4,
                quality=Quality._720,
                output_folder=tmp_path,
            )
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_yumeapi_download_service_rejects_unsupported_format(tmp_path) -> None:
    service = YumeApiDownloadService(base_url="http://127.0.0.1:8000")

    with pytest.raises(DownloadFailed, match="only supports"):
        await service.download(
            url="https://example.com/video",
            format_value=Formats.WEBM,
            quality=Quality._720,
            output_folder=tmp_path,
        )
