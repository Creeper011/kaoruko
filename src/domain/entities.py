from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import uuid

@dataclass
class DownloadResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filepath: Optional[Path] = None
    link: Optional[str] = None
    file_size: Optional[int] = None
    elapsed: Optional[float] = None

    def is_success(self) -> bool:
        return self.filepath is not None and self.file_size is not None

@dataclass
class SpeedMediaResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    factor: float = 1.0
    filepath: Optional[Path] = None
    temp_dir: Optional[Path] = None
    elapsed: Optional[float] = None
    file_size: Optional[int] = None
    drive_link: Optional[str] = None
    is_audio: bool = False

    def is_audio_file(self) -> bool:
        return self.is_audio and self.filepath is not None
