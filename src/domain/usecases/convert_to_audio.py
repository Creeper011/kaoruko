import time
import discord
import shutil
import asyncio
from uuid import uuid4
from typing import Tuple
from pathlib import Path
from moviepy import VideoFileClip
from src.config.settings import SettingsManager
from src.infrastructure.constants.error_types import ErrorTypes
from src.core.models import Result

class ConvertToAudio():
    def __init__(self):
        self.ALLOWED_CONTENT_TYPES = [
            "video/mp4",
            "video/x-matroska",
            "video/quicktime",
            "video/webm",
            "video/avi",
            "video/mpeg",
            "video/ogg",
        ]
        self.settings = SettingsManager()
        self.temp_dir = self.settings.get({"ConvertToAudio": "temp_dir"})
        
    def _create_process_path(self):
        process_uuid = uuid4()
        process_path = Path(self.temp_dir) / str(process_uuid)
        process_path.mkdir(parents=True, exist_ok=True)
        return process_path

    def _cleanup_process_path(self, process_path: Path):
        try:
            if process_path and process_path.exists():
                shutil.rmtree(process_path, ignore_errors=True)
        except:
            pass
        
    async def toAudioFromAttachment(self, attachment: discord.Attachment) -> Tuple[Result, Path, Path, float]:
        if attachment.content_type not in self.ALLOWED_CONTENT_TYPES:
            return Result.failure(error="Content_type not allowed", 
                                  type=ErrorTypes.INVALID_FILE_TYPE), None, None

        start = time.time()

        folder = self._create_process_path()
        file_path = folder / attachment.filename
        await attachment.save(file_path)

        try:
            audio_path = await self._toAudio(file_path)
            elapsed = time.time() - start
            return Result.success(), audio_path, folder, elapsed
        except Exception as error:
            self._cleanup_process_path(folder)
            return Result.failure(f"Unexpected Error: {str(error)}",
                                  type=ErrorTypes.UNKNOWN), None, None

    async def _toAudio(self, filepath: Path) -> Path:
        def convert():
            video = VideoFileClip(str(filepath))
            audio = video.audio
            audio_path = filepath.with_suffix(".mp3")
            audio.write_audiofile(str(audio_path))
            video.close()
            audio.close()
            return audio_path

        return await asyncio.to_thread(convert)