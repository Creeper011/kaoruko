
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DownloadResult():
    file_path: Path = None
    drive_link: str = None
    elapsed: float = None
    download_path: Path = None
    speed_elapsed: float = None
    resolution: str = None
    frame_rate: float = None
    is_audio: bool = None