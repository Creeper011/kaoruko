
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AudioExtractionResult():
    file_path: Path = None
    drive_link: str = None
    elapsed: float = None
    speed_elapsed: float = None