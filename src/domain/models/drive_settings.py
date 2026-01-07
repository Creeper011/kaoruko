from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DriveSettings:
    credentials_path: Path
    folder_id: str