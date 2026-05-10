from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class DriveSettings:
    credentials_path: Optional[Path] = None
    folder_id: Optional[str] = None