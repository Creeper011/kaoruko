from dataclasses import dataclass, field
from typing import List

DEFAULT_DOWNLOAD_API_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_DOWNLOAD_API_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_DOWNLOAD_API_TIMEOUT_SECONDS = 1200.0

@dataclass(frozen=True)
class DownloadSettings:
    """All settings related to downloading files"""
    file_size_limit: int = 25 * 1024 * 1024 # 25MB default
    blacklist_sites: List[str] = field(default_factory=list)
    api_base_url: str = DEFAULT_DOWNLOAD_API_BASE_URL
    api_poll_interval_seconds: float = DEFAULT_DOWNLOAD_API_POLL_INTERVAL_SECONDS
    api_timeout_seconds: float = DEFAULT_DOWNLOAD_API_TIMEOUT_SECONDS
