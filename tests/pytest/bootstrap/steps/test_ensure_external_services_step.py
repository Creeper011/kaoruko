import pytest
from aiohttp import web

from src.bootstrap.steps.ensure_external_services_step import ensure_external_services
from src.domain.models.settings import DownloadSettings
from src.services.config.models import ApplicationSettings


async def _start_test_server(app: web.Application, port: int) -> web.AppRunner:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    return runner


def _build_settings(base_url: str) -> ApplicationSettings:
    return ApplicationSettings(
        download=DownloadSettings(download_api=base_url),
    )


@pytest.mark.asyncio
async def test_ensure_external_services_accepts_available_service_root(unused_tcp_port: int) -> None:
    app = web.Application()

    runner = await _start_test_server(app, unused_tcp_port)

    try:
        settings = _build_settings(f"http://127.0.0.1:{unused_tcp_port}")
        await ensure_external_services(settings)
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_ensure_external_services_accepts_successful_service_root(unused_tcp_port: int) -> None:
    async def get_root(_: web.Request) -> web.Response:
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/", get_root)

    runner = await _start_test_server(app, unused_tcp_port)

    try:
        settings = _build_settings(f"http://127.0.0.1:{unused_tcp_port}")
        await ensure_external_services(settings)
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_ensure_external_services_raises_when_service_is_unavailable(unused_tcp_port: int) -> None:
    settings = _build_settings(f"http://127.0.0.1:{unused_tcp_port}")

    with pytest.raises(RuntimeError, match="YumeApi is not available"):
        await ensure_external_services(settings)
