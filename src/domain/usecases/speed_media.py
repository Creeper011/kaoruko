import asyncio
import mimetypes
import time
import uuid
import logging
import shutil
from pathlib import Path
from src.domain.entities import SpeedMediaResult
from src.infrastructure.constants import Result, ErrorTypes
from src.domain.ports.drive_port import DrivePort
from src.domain.ports.speed_service_port import SpeedServicePort

logger = logging.getLogger(__name__)

class SpeedControlMedia():
    def __init__(self, drive_port: DrivePort, audio_speed_port: SpeedServicePort, video_speed_port: SpeedServicePort):
        self.FILE_SIZE_LIMIT = 120 * 1024 * 1024  # 120 MB
        self.drive = drive_port
        self.audio_speed_service = audio_speed_port
        self.video_speed_service = video_speed_port
        # Supported MIME types
        self.SUPPORTED_VIDEO_MIMES = [
            "video/mp4", "video/avi", "video/quicktime", "video/webm", 
            "video/x-matroska", "video/x-msvideo", "video/3gpp", "video/x-flv"
        ]
        
        self.SUPPORTED_AUDIO_MIMES = [
            "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", 
            "audio/flac", "audio/aac", "audio/ogg", "audio/x-m4a", "audio/mp4"
        ]

    def _create_temp_dir(self) -> Path:
        """Create a temporary directory for processing"""
        temp_dir = Path("temp/speed_control")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        unique_id = str(uuid.uuid4())
        temp_dir = temp_dir / unique_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        return temp_dir

    def _get_mime_type(self, filepath: Path) -> tuple[str, bool, bool]:
        """Get mime type and determine if file is video or audio"""
        mime_type = mimetypes.guess_type(str(filepath))[0]
        if not mime_type:
            return None, False, False
        
        is_video = mime_type.startswith("video/")
        is_audio = mime_type.startswith("audio/")
        
        return mime_type, is_video, is_audio
    
    def _cleanup_temp_dir(self, temp_dir: Path) -> None:
        """Clean up temporary directory"""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory {temp_dir}: {e}")
    
    async def change_speed_from_stream(self, file_data: bytes, filename: str, content_type: str, speed: float, preserve_pitch: bool) -> Result:
        """
        Change the playback speed of a media file from binary data stream.

        Args:
            file_data (bytes): Binary data of the media file.
            filename (str): Original filename with extension.
            content_type (str): MIME type of the file.
            speed (float): Speed factor to apply (e.g., 1.5 for 1.5x speed).
            preserve_pitch (bool): Whether to maintain the original audio pitch
                when changing speed (True keeps pitch, False alters it proportionally).

        Returns:
            Result: A Result object containing a SpeedMediaResult on success,
                    or an error message and type on failure.
        """
        # Validate content type
        if not content_type or not (content_type.startswith("audio/") or content_type.startswith("video/")):
            logger.error(f"Unsupported content type: {content_type}")
            return Result.failure("Unsupported file type. Please upload an audio or video file.", ErrorTypes.INVALID_FILE_TYPE)
        
        temp_dir = self._create_temp_dir()
        
        try:
            # Save binary data to temporary file
            input_path = temp_dir / filename
            with open(input_path, 'wb') as file:
                file.write(file_data)
            
            # Process the file
            result = await self.change_speed(input_path, speed, preserve_pitch)
            
            return result
            
        except Exception as e:
            logger.exception(f"Unexpected error processing file {filename}: {e}")
            return Result.failure(f"Unexpected error: {e}", ErrorTypes.UNKNOWN)
        finally:
            # Always cleanup temp directory
            self._cleanup_temp_dir(temp_dir)

    async def change_speed(self, filepath: Path, speed: float, preserve_pitch: bool) -> Result:
        """
        Change the playback speed of an audio or video file.

        Args:
            filepath (Path): Path to the input media file.
            speed (float): Speed factor to apply (e.g., 1.5 for 1.5x speed).
            preserve_pitch (bool): If True, adjusts playback speed without altering
                the original pitch of the audio; if False, pitch changes with speed.

        Returns:
            Result: A Result object containing a SpeedMediaResult on success,
                    or an error message and type on failure.

        Notes:
            - Supports specific audio and video MIME types.
            - If output file size exceeds the limit, it will be uploaded to the drive,
            and the drive link will be included in the result.
            - The filepath in the result always points to the local output file.
        """
        if not filepath.exists() or not filepath.is_file():
            logger.error(f"File not found: {filepath}")
            return Result.failure("File not found.", ErrorTypes.FILE_NOT_FOUND)
        
        mime_type, is_video, is_audio = self._get_mime_type(filepath)
        
        if not mime_type:
            logger.error(f"Unsupported or unidentified MIME type: {filepath}")
            return Result.failure("Unsupported MIME type.", ErrorTypes.INVALID_FILE_TYPE)
        
        if is_video and mime_type not in self.SUPPORTED_VIDEO_MIMES:
            logger.error(f"Unsupported video MIME type: {mime_type}")
            return Result.failure("Unsupported video MIME type.", ErrorTypes.INVALID_FILE_TYPE)
        
        if is_audio and mime_type not in self.SUPPORTED_AUDIO_MIMES:
            logger.error(f"Unsupported audio MIME type: {mime_type}")
            return Result.failure("Unsupported audio MIME type.", ErrorTypes.INVALID_FILE_TYPE)
        
        temp_dir = self._create_temp_dir()
        default_output_path = temp_dir / f"{filepath.stem}{filepath.suffix}"
        
        try:
            start_time = time.time()

            logger.debug(f"Is this file is a video? {is_video}")
            
            if is_video:
                success, error, output_path = await asyncio.to_thread(
                    self.video_speed_service.process, filepath, default_output_path, speed, preserve_pitch
                )
            elif is_audio:
                success, error, output_path = await asyncio.to_thread(
                    self.audio_speed_service.process, filepath, default_output_path, speed, preserve_pitch
                )
            else:
                logger.error(f"File is neither audio nor video: {filepath}")
                return Result.failure("File is neither audio nor video.", ErrorTypes.INVALID_FILE_TYPE)
            
            if not success:
                logger.error(f"Processing failed: {error}")
                return Result.failure(f"Processing failed: {error}", ErrorTypes.UNKNOWN)
            
            drive_link = None
            if output_path.stat().st_size > self.FILE_SIZE_LIMIT:
                drive_link = await self.drive.uploadToDrive(str(output_path))
            
            elapsed_time = time.time() - start_time
            
            result_obj = SpeedMediaResult(
                factor=speed,
                elapsed=elapsed_time,
                temp_dir=temp_dir,
                filepath=output_path,
                file_size=output_path.stat().st_size,
                drive_link=drive_link,
                is_audio=is_audio
            )
            
            return Result.success(result_obj)
        
        except Exception as e:
            logger.exception(f"Unexpected error processing file {filepath}: {e}")
            return Result.failure(f"Unexpected error: {e}", ErrorTypes.UNKNOWN)