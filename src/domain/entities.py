from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class DownloadResult:
    filepath: Optional[str] = None
    link: Optional[str] = None
    file_size: Optional[int] = None
    elapsed: Optional[float] = None

@dataclass
class SpeedAudioResult:
    factor: float = None
    filepath: Optional[Path] = None
    elapsed: float = None
    file_size: Optional[int] = None
    drive_link: Optional[str] = None