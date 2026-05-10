import asyncio
import logging
from logging import Logger

import aiohttp

from src.services.config.models import ApplicationSettings


async def ensure_external_services(settings: ApplicationSettings) -> None:
    """Ensures that external services are available."""
    if settings.download is None:
        raise RuntimeError("Download settings must be configured to ensure external services.")

    logger = logging.getLogger("EnsureExternalServicesStep")
    logger.info("Ensuring external services")
    await _ensure_http_service(
        service_name="YumeApi",
        base_url=settings.download.download_api,
        logger=logger,
    )
    logger.info("External services ensured successfully")


async def _ensure_http_service(service_name: str, base_url: str, logger: Logger) -> None:
    """Ensures a HTTP service is available."""
    service_url = base_url.rstrip("/")
    if not service_url:
        raise RuntimeError(f"{service_name} base url must be configured.")

    timeout = aiohttp.ClientTimeout(total=3.0)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(service_url) as response:
                if response.status >= 500:
                    raise RuntimeError(
                        f"{service_name} returned status {response.status} at {service_url}."
                    )
    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        raise RuntimeError(f"{service_name} is not available at {service_url}: {error}") from None

    logger.info("%s is available at %s", service_name, service_url)
