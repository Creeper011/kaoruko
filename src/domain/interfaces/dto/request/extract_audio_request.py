from dataclasses import dataclass

@dataclass
class ExtractAudioRequest():
    url: str
    file_limit: int = None
    file_size: int = None