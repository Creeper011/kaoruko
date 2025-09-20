import shutil
import uuid
import time
import logging
import requests
from pathlib import Path
from moviepy import VideoFileClip
from src.domain.interfaces.dto.output.extract_audio_output import ExtractAudioOutput

logger = logging.getLogger(__name__)


class AudioExtractService:
    """
    Service for extracting audio from video files downloaded from URLs.
    
    This service downloads a video file from a given URL, extracts its audio track,
    and provides cleanup functionality for temporary files.
    """
    
    def __init__(self, url: str):
        """
        Initialize the AudioExtractService with a video URL.
        
        Args:
            url (str): The URL of the video file to process
        """
        logger.debug(f"Initializing AudioExtractService with URL: {url}")
        
        self.url = url
        self.session_id = uuid.uuid4()
        self.temp_dir = Path(f"./temp/extract_audio/{self.session_id}")
        self.start_time = time.time()
        
        logger.debug(f"Session ID generated: {self.session_id}")
        logger.debug(f"Temporary directory set to: {self.temp_dir}")

    async def __aenter__(self) -> "AudioExtractService":
        """
        Async context manager entry point.
        
        Creates the temporary directory structure.
        
        Returns:
            AudioExtractService: The service instance
        """
        logger.debug(f"Creating temporary directory: {self.temp_dir}")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Temporary directory created successfully")
        return self

    async def __aexit__(self, exc_type, exc_val, tb) -> None:
        """
        Async context manager exit point.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            tb: Traceback (if any)
        """
        logger.debug("Exiting AudioExtractService context")
        if exc_type:
            logger.error(f"Exception occurred during processing: {exc_type.__name__}: {exc_val}")

    def _cleanup(self):
        """
        Clean up only the session-specific temporary directory.
        
        Removes the folder corresponding to this session_id and all its contents.
        """
        logger.debug(f"Starting cleanup for session directory: {self.temp_dir}")
        
        if self.temp_dir.exists() and self.temp_dir.is_dir():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Session directory {self.temp_dir} removed successfully")
            except Exception as e:
                logger.error(f"Failed to remove session directory {self.temp_dir}: {e}")
        else:
            logger.debug("No session directory found to clean up")

    def _download_video(self) -> tuple[Path, str]:
        """
        Download video file from the configured URL.
        
        Returns:
            tuple[Path, str]: A tuple containing the path to the downloaded file and original filename
            
        Raises:
            requests.RequestException: If the download fails
        """
        logger.debug(f"Starting video download from URL: {self.url}")
        
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            
            content_size = len(response.content)
            logger.debug(f"Video downloaded successfully, size: {content_size} bytes")
            
            original_filename = Path(self.url).name
            if not original_filename or '.' not in original_filename:
                original_filename = "video.mp4"
                logger.debug(f"No filename in URL, using fallback: {original_filename}")
            else:
                logger.debug(f"Original filename extracted: {original_filename}")
            
            video_path = self.temp_dir / original_filename
            logger.debug(f"Saving video to: {video_path}")
            
            with open(video_path, "wb") as f:
                f.write(response.content)
            
            logger.debug("Video file saved successfully")
            return (video_path, original_filename)
            
        except requests.RequestException as e:
            logger.error(f"Failed to download video: {e}")
            raise

    def _process_video(self) -> Path:
        """
        Process the downloaded video file and extract its audio track.
        
        Returns:
            Path: Path to the extracted audio file
            
        Raises:
            Exception: If video processing fails
        """
        logger.debug("Starting video processing...")
        
        video_path, original_filename = self._download_video()
        logger.debug(f"Processing video file: {video_path}")
        
        try:
            logger.debug("Loading video clip with MoviePy")
            clip = VideoFileClip(str(video_path))
            
            audio_filename = Path(original_filename).stem + ".mp3"
            audio_path = self.temp_dir / audio_filename
            
            logger.debug(f"Extracting audio to: {audio_path}")
            
            clip.audio.write_audiofile(str(audio_path))
            clip.close()
            
            logger.debug("Audio extraction completed successfully")
            
            if audio_path.exists():
                file_size = audio_path.stat().st_size
                logger.debug(f"Audio file size: {file_size} bytes")
            
            return audio_path
            
        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            raise

    async def get_response(self) -> ExtractAudioOutput:
        """
        Main method to extract audio from video and return the result.
        
        Returns:
            ExtractAudioOutput: Contains file path, processing time, cleanup function, and file size
            
        Raises:
            Exception: If audio extraction fails
        """
        logger.debug("Starting audio extraction process...")
        
        try:
            audio_path = self._process_video()
            
            elapsed_time = time.time() - self.start_time
            file_size = audio_path.stat().st_size if audio_path.exists() else 0
            
            logger.debug(f"Audio extraction completed in {elapsed_time:.2f} seconds")
            logger.debug(f"Output file: {audio_path}")
            logger.debug(f"File size: {file_size} bytes")
            
            return ExtractAudioOutput(
                file_path=str(audio_path),
                elapsed=elapsed_time,
                cleanup=self._cleanup,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise