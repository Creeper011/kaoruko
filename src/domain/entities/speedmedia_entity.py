from dataclasses import dataclass
from pathlib import Path

@dataclass
class SpeedMediaResult:
    file_path: Path = None
    drive_path: str = None
    elapsed: float = None
    exception: Exception = None