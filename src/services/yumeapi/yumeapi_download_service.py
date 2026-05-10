import asyncio
from collections.abc import Awaitable, Callable
import logging
from pathlib import Path
from typing import Any, Optional

import aiohttp

from src.application.protocols import DownloadServiceProtocol
from src.domain.enum import Formats, Quality
from src.domain.exceptions.download_exceptions import DownloadFailed
from src.domain.models import DownloadedFile


class YumeApiDownloadService(DownloadServiceProtocol):
    """Downloads media by delegating the job to the external yumeapi service."""

    SUPPORTED_FORMATS: frozenset[Formats] = frozenset({Formats.MP3, Formats.MP4})
    QUALITY_MAP: dict[Quality, str] = {
        Quality._360: "360p",
        Quality._480: "480p",
        Quality._720: "720p",
        Quality._1080: "1080p",
    }

    def __init__(
        self,
        base_url: str,
        status_poll_interval_seconds: float = 1.0,
        job_timeout_seconds: float = 1200.0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.base_url = base_url.rstrip("/")
        self.status_poll_interval_seconds = status_poll_interval_seconds
        self.job_timeout_seconds = job_timeout_seconds

    async def download(
        self,
        url: str,
        format_value: str | Formats | None,
        quality: Quality,
        output_folder: Path,
        progress_callback: Callable[[float], Awaitable[None]] | None = None,
    ) -> DownloadedFile:
        selected_format = self._normalize_format(format_value)
        payload = self._build_payload(url, selected_format, quality)
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_connect=10)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                job_id = await self._create_job(session, payload)
                job_status = await self._wait_for_completion(session, job_id, progress_callback=progress_callback)
                return await self._download_file(session, job_id, job_status, output_folder)
        except DownloadFailed:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            raise DownloadFailed(f"Failed to contact download API at {self.base_url}: {error}") from error

    def _normalize_format(self, format_value: str | Formats | None) -> Formats:
        if format_value is None:
            return Formats.MP4

        if isinstance(format_value, Formats):
            selected_format = format_value
        else:
            try:
                selected_format = Formats(format_value)
            except ValueError as error:
                raise DownloadFailed(f"Unsupported format requested: {format_value}") from error

        if selected_format not in self.SUPPORTED_FORMATS:
            supported = ", ".join(format_item.value for format_item in sorted(self.SUPPORTED_FORMATS, key=lambda item: item.value))
            raise DownloadFailed(
                f"The configured download API only supports: {supported}. Requested: {selected_format.value}"
            )

        return selected_format

    def _build_payload(self, url: str, format_value: Formats, quality: Quality) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": url,
            "format": format_value.value,
        }

        if format_value == Formats.MP4:
            api_quality = self.QUALITY_MAP.get(quality)
            if api_quality is None:
                supported = ", ".join(value for _, value in sorted(self.QUALITY_MAP.items(), key=lambda item: item[1]))
                raise DownloadFailed(
                    f"The configured download API only supports video qualities: {supported}. Requested: {quality.value}"
                )
            payload["quality"] = api_quality

        return payload

    async def _create_job(self, session: aiohttp.ClientSession, payload: dict[str, Any]) -> str:
        response_data = await self._request_json(
            session,
            "post",
            "/download",
            json=payload,
        )

        job_id = response_data.get("id")
        if not isinstance(job_id, str) or not job_id:
            raise DownloadFailed("Download API returned an invalid job id.")

        self.logger.info("Created download job %s for %s", job_id, payload["url"])
        return job_id

    async def _wait_for_completion(
        self,
        session: aiohttp.ClientSession,
        job_id: str,
        progress_callback: Callable[[float], Awaitable[None]] | None = None,
    ) -> dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + self.job_timeout_seconds
        last_progress: float | None = None

        while True:
            status_payload = await self._request_json(session, "get", f"/download/{job_id}")
            job_status = str(status_payload.get("status", "")).lower()
            progress = self._normalize_progress(status_payload.get("progress"))

            if progress is not None and progress != last_progress:
                last_progress = progress
                if progress_callback is not None:
                    await progress_callback(progress)

            if job_status == "completed":
                if last_progress != 100.0 and progress_callback is not None:
                    await progress_callback(100.0)
                return status_payload

            if job_status == "failed":
                error_message = status_payload.get("error") or "The download API reported a failure."
                raise DownloadFailed(str(error_message))

            if job_status not in {"pending", "running"}:
                raise DownloadFailed(f"Download API returned an unknown job status: {job_status or 'empty'}")

            if asyncio.get_running_loop().time() >= deadline:
                raise DownloadFailed(
                    f"Download API job {job_id} timed out after {self.job_timeout_seconds:.0f} seconds."
                )

            await asyncio.sleep(self.status_poll_interval_seconds)

    def _normalize_progress(self, raw_progress: Any) -> float | None:
        try:
            progress = float(raw_progress)
        except (TypeError, ValueError):
            return None

        return max(0.0, min(progress, 100.0))

    async def _download_file(
        self,
        session: aiohttp.ClientSession,
        job_id: str,
        job_status: dict[str, Any],
        output_folder: Path,
    ) -> DownloadedFile:
        output_folder.mkdir(parents=True, exist_ok=True)
        filename = self._resolve_filename(job_status)
        destination = output_folder / filename
        headers = {"accept": "application/octet-stream"}

        async with session.get(f"{self.base_url}/download/{job_id}/file", headers=headers) as response:
            if response.status >= 400:
                message = await self._extract_error_message(response)
                raise DownloadFailed(message)

            bytes_written = 0
            with destination.open("wb") as output_file:
                async for chunk in response.content.iter_chunked(64 * 1024):
                    bytes_written += len(chunk)
                    output_file.write(chunk)

        self.logger.info("Downloaded file %s from job %s", destination, job_id)
        return DownloadedFile(file_path=destination, file_size=bytes_written)

    def _resolve_filename(self, job_status: dict[str, Any]) -> str:
        raw_filename = str(job_status.get("filename") or "").strip()
        if raw_filename:
            return Path(raw_filename).name
        return "downloaded_file"

    async def _request_json(
        self,
        session: aiohttp.ClientSession,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        headers = {
            "accept": "application/json",
        }

        if "json" in kwargs:
            headers["content-type"] = "application/json"

        async with session.request(
            method=method.upper(),
            url=f"{self.base_url}{path}",
            headers=headers,
            **kwargs,
        ) as response:
            data = await self._safe_parse_json(response)
            if response.status >= 400:
                message = data.get("error") if isinstance(data, dict) else None
                raise DownloadFailed(str(message or f"Download API request failed with status {response.status}."))

            if not isinstance(data, dict):
                raise DownloadFailed("Download API returned an invalid JSON response.")

            return data

    async def _safe_parse_json(self, response: aiohttp.ClientResponse) -> Any:
        try:
            return await response.json(content_type=None)
        except Exception:
            text = await response.text()
            return {"error": text.strip()} if text else {}

    async def _extract_error_message(self, response: aiohttp.ClientResponse) -> str:
        data = await self._safe_parse_json(response)
        if isinstance(data, dict) and data.get("error"):
            return str(data["error"])
        return f"Download API request failed with status {response.status}."
