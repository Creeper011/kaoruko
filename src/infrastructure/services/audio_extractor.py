import asyncio
import os
from moviepy import VideoFileClip

class AudioExtractor():
    def __init__(self):
        pass

    def extract_audio_sync(self, file_path: str):
        if not os.path.exists(file_path):
            return None

        output_path = file_path.replace(".mp4", ".mp3")
        video = VideoFileClip(file_path)
        audio = video.audio
        audio.write_audiofile(output_path)
        return output_path

    async def extract_audio_async(self, file_path: str):
        await asyncio.to_thread(self.extract_audio_sync, file_path)