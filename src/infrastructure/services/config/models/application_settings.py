from typing import Optional
from discord import Intents
from dataclasses import dataclass
from src.domain.models.settings.download_settings import DownloadSettings
from src.domain.models.settings.drive_settings import DriveSettings

@dataclass(frozen=True)
class BotSettings():
    """All settings related to discord bot"""
    prefix: Optional[str] | None = None
    token: Optional[str] | None = None
    intents: Optional[Intents] | None = None

@dataclass(frozen=True)
class ApplicationSettings():
    """All settings"""
    bot_settings: Optional[BotSettings] = None
    download_settings: Optional[DownloadSettings] = None
    drive_settings: Optional[DriveSettings] = None