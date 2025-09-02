import asyncio
import os
import shutil
import uuid
import logging
import time
import discord
from pathlib import Path
from src.infrastructure.services import AudioCrusher
from src.infrastructure.services import DriveLoader
from src.domain.entities.bitcrusher_entity import BitCrushResult
from src.domain.services.media_validation import MediaValidationService

logger = logging.getLogger(__name__)

class BitCrusherUsecase:
    def __init__(self, bit_depth: int, downsample_rate: int, max_media_size: int = 120 * 1024 * 1024):
        self.bit_depth = bit_depth
        self.downsample_rate = downsample_rate
        self.max_media_size = max_media_size
        self.temp_dir = Path("temp/bit_crusher")
        self.session_id = str(uuid.uuid4())
        self.drive = DriveLoader().get_drive()
        self.media_validator = MediaValidationService()

    def _cleanup(self) -> bool:
        try:
            session_path = self.temp_dir / self.session_id
            shutil.rmtree(session_path, ignore_errors=True)
            return True
        except Exception as error:
            logger.error(f"Error cleaning up temporary files: {error}")
            return False
        
    def _create_temp_directory(self) -> Path:
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        return self.temp_dir
    
    def _create_session_temp_directory(self) -> Path:
        session_temp_dir = self.temp_dir / self.session_id
        session_temp_dir.mkdir(parents=True, exist_ok=True)
        return session_temp_dir

    async def crush_media_attachement(self, attachment: discord.Attachment) -> BitCrushResult:
        temp_dir = self._create_temp_directory()
        session_temp_dir = self._create_session_temp_directory()
        input_path = session_temp_dir / attachment.filename

        await attachment.save(input_path)
        logger.debug(f"Attachment saved to {input_path}")

        return await self.crush_media(Path(os.path.abspath(input_path)))

    async def crush_media(self, filepath: Path) -> BitCrushResult:
        start = time.time()

        if not filepath.exists():
            raise FileNotFoundError(f"{filepath} not found")

        temp_dir = self._create_temp_directory()
        session_temp_dir = self._create_session_temp_directory()
        output_path = session_temp_dir / f"{filepath.stem}_crushed{filepath.suffix}"

        # Validate media file using domain service
        is_valid, error_msg = self.media_validator.validate_media_file(filepath)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Check if it's an audio file (bit crusher only supports audio)
        if not self.media_validator.is_audio_file(filepath):
            raise ValueError(f"Bit crusher only supports audio files, got: {filepath.suffix}")
        
        crusher = AudioCrusher(bit_depth=self.bit_depth, downsample_rate=self.downsample_rate)
        
        logger.debug(f"Processing {filepath} with {crusher.__class__.__name__}")

        await asyncio.to_thread(crusher.process, filepath, output_path)

        drive_link = None
        if output_path.stat().st_size > self.max_media_size:
            drive_link = await self.drive.uploadToDrive(output_path)

        return BitCrushResult(
            file_path=output_path,
            drive_link=drive_link,
            elapsed=time.time() - start
        )
