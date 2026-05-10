from dataclasses import dataclass, field
from typing import List

DEFAULT_DOWNLOAD_API = "http://127.0.0.1:8000"
DEFAULT_DOWNLOAD_API_POLL_INTERVAL = 1.0
DEFAULT_DOWNLOAD_API_TIMEOUT = 1200.0

@dataclass(frozen=True)
class DownloadSettings:
    download_api: str = DEFAULT_DOWNLOAD_API
    api_poll_interval: float = DEFAULT_DOWNLOAD_API_POLL_INTERVAL
    api_timeout: float = DEFAULT_DOWNLOAD_API_TIMEOUT
    file_size_limit: int = 25 * 1024 * 1024
    blacklist_sites: List[str] = field(default_factory=list)
