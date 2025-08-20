from dataclasses import dataclass

@dataclass
class SpeedMediaResult:
    file_path: str = None
    drive_path: str = None
    elapsed: float = None
    exception: Exception = None