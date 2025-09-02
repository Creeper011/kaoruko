import asyncio
import os
import shutil
import time
import logging
from pathlib import Path
import uuid
from discord import Attachment
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from src.domain.entities.speedmedia_entity import SpeedMediaResult
from src.domain.exceptions.speedmedia_exceptions import GenericError, FailedToUploadDrive, InvalidFileType
from src.infrastructure.services.speed import VideoSpeedService, AudioSpeedService
from src.infrastructure.services import DriveLoader
from src.domain.services.media_validation import MediaValidationService, MediaType

logger = logging.getLogger(__name__)

class SpeedMedia:
    def __init__(self):
        self.audio_service = AudioSpeedService()
        self.video_service = VideoSpeedService()
        self.drive = DriveLoader().get_drive()
        self.session_id = str(uuid.uuid4())
        self.temp_dir = Path("temp/speed_control")
        self.max_file_size = 120 * 1024 * 1024
        self.media_validator = MediaValidationService()

    def _cleanup(self) -> bool:
        try:
            session_path = self.temp_dir / self.session_id
            if session_path.exists():
                shutil.rmtree(session_path)
            logger.debug("Temporary files cleaned up.")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
            return False

    def _create_temp_directory(self) -> Path:
        if not self.temp_dir.exists():
            self.temp_dir.mkdir()
        return self.temp_dir

    def _create_session_temp_directory(self) -> Path:
        session_temp_dir = self.temp_dir / self.session_id
        if not session_temp_dir.exists():
            session_temp_dir.mkdir()
        return session_temp_dir

    def _resolve_format(self, file_path: Path) -> str:
        """Resolve file format using domain validation service"""
        logger.debug(f"Resolving format for {file_path}")
        
        # Validate the media file first
        is_valid, error_msg = self.media_validator.validate_media_file(file_path)
        if not is_valid:
            raise InvalidFileType(error_msg)
        
        # Get media type using domain service
        media_type = self.media_validator.get_media_type(file_path)
        
        if media_type == MediaType.AUDIO:
            return 'audio'
        elif media_type == MediaType.VIDEO:
            return 'video'
        else:
            raise InvalidFileType(f"Unsupported media type for file: {file_path}")

    def preserve_metadata(self, original_path: Path, processed_path: Path):
        """Preserve metadata between original and processed files"""
        try:
            original_ext = original_path.suffix.lower()
            processed_ext = processed_path.suffix.lower()
            
            if original_ext == '.mp3' and processed_ext == '.mp3':
                original_audio = MP3(str(original_path), ID3=ID3)
                processed_audio = MP3(str(processed_path), ID3=ID3)
                if original_audio.tags:
                    for key, value in original_audio.tags.items():
                        processed_audio.tags[key] = value
                    processed_audio.save()
                    logger.debug("MP3 metadata preserved.")

            elif original_ext == '.mp4' and processed_ext == '.mp4':
                original_audio = MP4(str(original_path))
                processed_audio = MP4(str(processed_path))
                if original_audio.tags:
                    for key, value in original_audio.tags.items():
                        processed_audio.tags[key] = value
                    processed_audio.save()
                    logger.debug("MP4 metadata preserved.")

            elif original_ext == '.flac' and processed_ext == '.flac':
                original_audio = FLAC(str(original_path))
                processed_audio = FLAC(str(processed_path))
                for key, value in original_audio.items():
                    processed_audio[key] = value
                processed_audio.save()
                logger.debug("FLAC metadata preserved.")

        except Exception as e:
            logger.debug(f"Warning: Could not preserve metadata: {e}")

    async def change_speed_attachment(self, attachment: Attachment, speed: float, preserve_pitch: bool) -> SpeedMediaResult:
        start_time = time.time()
        try:
            temp_input = Path(attachment.filename)
            await attachment.save(temp_input)
            logger.debug(f"Attachment saved to {temp_input}")

            result = await self.change_speed(temp_input, speed, preserve_pitch)

            if temp_input.exists():
                temp_input.unlink()
                logger.debug(f"Temporary file {temp_input} removed.")

            result.elapsed = time.time() - start_time
            return result

        except (GenericError, FailedToUploadDrive, InvalidFileType) as e:
            logger.debug(f"Specific error changing speed for attachment {attachment.filename}: {e}")
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)
        except Exception as e:
            logger.debug(f"Unexpected error changing speed for attachment {attachment.filename}: {e}")
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)


    async def change_speed(self, file_path: Path, speed: float, preserve_pitch: bool, not_upload_to_drive: bool = None) -> SpeedMediaResult:
        start_time = time.time()

        session_path = self._create_session_temp_directory()

        output_filename = f"{speed}x - {file_path.stem}{file_path.suffix}"
        output_path = session_path / output_filename

        try:
            file_format = self._resolve_format(file_path)
            logger.debug(f"File format resolved as {file_format}")

            if file_format == 'audio':
                success, error, output_path = await asyncio.to_thread(self.audio_service.process, file_path, output_path, speed, preserve_pitch)
            elif file_format == 'video':
                success, error, output_path = await asyncio.to_thread(self.video_service.process, file_path, output_path, speed, preserve_pitch)
            else:
                raise InvalidFileType(f"Unsupported file type for file: {file_path}")

            if not success:
                raise GenericError(f"Speed change failed: {error}")

            self.preserve_metadata(file_path, output_path)

            file_size = output_path.stat().st_size
            drive_path = None

            if not_upload_to_drive is None or not_upload_to_drive is False:
                if file_size > self.max_file_size:
                    try:
                        drive_path = await self.drive.uploadToDrive(output_path)
                        logger.debug(f"File uploaded to Drive (size: {file_size / 1024 / 1024:.2f}MB): {drive_path}")
                    except Exception as e:
                        raise FailedToUploadDrive(f"Failed to upload {output_path} to Drive: {e}")

                return SpeedMediaResult(file_path=output_path, drive_path=drive_path, elapsed=time.time() - start_time)

            return SpeedMediaResult(file_path=output_path, elapsed=time.time() - start_time)
        
        except (GenericError, FailedToUploadDrive, InvalidFileType) as e:
            logger.debug(f"Specific error processing file {file_path}: {e}")
            self._cleanup()
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)
        except Exception as e:
            logger.debug(f"Unexpected error processing file {file_path}: {e}")
            self._cleanup()
            return SpeedMediaResult(file_path=None, drive_path=None, elapsed=time.time() - start_time, exception=e)
        finally:
            # Cleanup is handled by the caller or can be done here if needed
            pass
