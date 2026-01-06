from typing import Optional
from discord import Intents
from dataclasses import dataclass
from src.domain.models.download_settings import DownloadSettings

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