from src.domain.usecases import DownloaderService, SpeedControlMedia
from src.infrastructure.adapters import DownloaderAdapter, DriveAdapter, AudioSpeedAdapter, VideoSpeedAdapter

class ServiceProvider:
    def __init__(self):
        self._drive_adapter = DriveAdapter()
        self._audio_speed_adapter = AudioSpeedAdapter()
        self._video_speed_adapter = VideoSpeedAdapter()

    def get_downloader_service(self, url: str, format: str, cancel_at_seconds: int = 240) -> DownloaderService:
        return DownloaderService(
            url=url,
            format=format,
            drive_port=self._drive_adapter,
            cancel_at_seconds=cancel_at_seconds
        )

    def get_speed_control_media(self) -> SpeedControlMedia:
        return SpeedControlMedia(
            drive_port=self._drive_adapter,
            audio_speed_port=self._audio_speed_adapter,
            video_speed_port=self._video_speed_adapter
        )

    def get_drive_adapter(self) -> DriveAdapter:
        return self._drive_adapter