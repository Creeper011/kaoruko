from dataclasses import dataclass

@dataclass
class DownloadRequest:
    url: str
    format: str = "mp4"
    quality: str = "best"
    file_limit: int = 120 * 1024 * 1024
    should_transcode: bool = False
    verbose: bool = False