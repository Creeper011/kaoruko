from dataclasses import dataclass
from src.domain.models.settings import DiscordSettings, DownloadSettings, DriveSettings

@dataclass(frozen=True)
class ApplicationSettings:
    discord: DiscordSettings = None
    download: DownloadSettings = None
    drive: DriveSettings = None