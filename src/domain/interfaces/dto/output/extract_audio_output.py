from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExtractAudioOutput():
    file_path: Path = None
    drive_link: str = None
    elapsed: float = None
    file_size: int = None
    cleanup: callable = None