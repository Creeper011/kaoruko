
from dataclasses import dataclass

@dataclass
class DownloadResult():
    file_path: str = None
    drive_link: str = None
    elapsed: float = None
    download_path: str = None
    speed_elapsed: float = None
    resolution: str = None
    frame_rate: float = None