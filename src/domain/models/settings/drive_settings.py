from dataclasses import dataclass
from pathlib import Path # domain shouldn't know about Path's existence, but I'll keep it here for now.

@dataclass(frozen=True)
class DriveSettings:
    credentials_path: Path
    folder_id: str