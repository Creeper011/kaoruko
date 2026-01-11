from enum import Enum

class Formats(Enum):
    MP4 = "mp4"
    MP3 = "mp3"
    MKV = "mkv"
    WEBM = "webm"
    OGG = "ogg"
    
    def is_audio(self) -> bool:
        return self in {Formats.MP3, Formats.OGG}