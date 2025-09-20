from dataclasses import dataclass
from pathlib import Path

@dataclass
class DownloadOutput():
    file_path: Path = None
    drive_link: str = None
    elapsed: float = None
    filesize: int = None
    resolution: str = None
    frame_rate: float = None
    is_audio: bool = None
    #speed_output: object = None
    cleanup: callable = None
    #cleanup_speed_included: bool = False