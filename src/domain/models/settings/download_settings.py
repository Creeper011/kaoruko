from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class DownloadSettings:
    """All settings related to downloading files"""
    file_size_limit: int = 25 * 1024 * 1024 # 25MB default
    blacklist_sites: List[str] = field(default_factory=list)