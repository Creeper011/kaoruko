from dataclasses import dataclass

@dataclass
class DownloadRequest:
    url: str
    format: str = "mp4"
    quality: str = "best"