import mimetypes
from pathlib import Path
from typing import Set, Dict, Optional
import logging
from src.domain.enums.mediaType import MediaType

logger = logging.getLogger(__name__)

class MediaValidationService:
    """Domain service for validating media file formats and MIME types"""
    
    def __init__(self):
        # Supported audio extensions
        self.audio_extensions: Set[str] = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'
        }
        
        # Supported video extensions
        self.video_extensions: Set[str] = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts'
        }
        
        # MIME type mappings for validation
        self.supported_mime_types: Dict[str, MediaType] = {
            'audio/mpeg': MediaType.AUDIO,
            'audio/wav': MediaType.AUDIO,
            'audio/flac': MediaType.AUDIO,
            'audio/aac': MediaType.AUDIO,
            'audio/ogg': MediaType.AUDIO,
            'audio/mp4': MediaType.AUDIO,
            'audio/x-ms-wma': MediaType.AUDIO,
            'audio/opus': MediaType.AUDIO,
            'video/mp4': MediaType.VIDEO,
            'video/avi': MediaType.VIDEO,
            'video/x-matroska': MediaType.VIDEO,
            'video/quicktime': MediaType.VIDEO,
            'video/x-ms-wmv': MediaType.VIDEO,
            'video/x-flv': MediaType.VIDEO,
            'video/webm': MediaType.VIDEO,
            'video/3gpp': MediaType.VIDEO,
            'video/mp2t': MediaType.VIDEO,
        }
    
    def validate_file_path(self, file_path: Path) -> bool:
        """Validate if the file path exists and is a file"""
        if not file_path or not file_path.exists():
            logger.warning(f"File path does not exist: {file_path}")
            return False
        
        if not file_path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return False
        
        return True
    
    def get_media_type_from_mime(self, file_path: Path) -> Optional[MediaType]:
        """Get media type from MIME type detection"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        if not mime_type:
            logger.debug(f"Could not detect MIME type for: {file_path}")
            return None
        
        logger.debug(f"Detected MIME type for {file_path}: {mime_type}")
        return self.supported_mime_types.get(mime_type)
    
    def get_media_type_from_extension(self, file_path: Path) -> Optional[MediaType]:
        """Get media type from file extension"""
        extension = file_path.suffix.lower()
        
        if extension in self.audio_extensions:
            return MediaType.AUDIO
        elif extension in self.video_extensions:
            return MediaType.VIDEO
        
        logger.debug(f"Unsupported file extension: {extension}")
        return None
    
    def get_media_type(self, file_path: Path) -> MediaType:
        """Get media type with fallback from MIME type to extension"""
        # First try MIME type detection
        media_type = self.get_media_type_from_mime(file_path)
        
        if media_type:
            return media_type
        
        # Fallback to extension-based detection
        media_type = self.get_media_type_from_extension(file_path)
        
        if media_type:
            return media_type
        
        return MediaType.UNSUPPORTED
    
    def is_audio_file(self, file_path: Path) -> bool:
        """Check if file is an audio file"""
        return self.get_media_type(file_path) == MediaType.AUDIO
    
    def is_video_file(self, file_path: Path) -> bool:
        """Check if file is a video file"""
        return self.get_media_type(file_path) == MediaType.VIDEO
    
    def is_supported_media(self, file_path: Path) -> bool:
        """Check if file is a supported media type"""
        media_type = self.get_media_type(file_path)
        return media_type in [MediaType.AUDIO, MediaType.VIDEO]
    
    def validate_media_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Comprehensive validation of a media file
        Returns: (is_valid, error_message)
        """
        # Check if file exists and is valid
        if not self.validate_file_path(file_path):
            return False, f"Invalid file path: {file_path}"
        
        # Check if it's a supported media type
        if not self.is_supported_media(file_path):
            return False, f"Unsupported media format: {file_path.suffix}"
        
        return True, None
    
    def get_supported_extensions(self) -> Dict[str, Set[str]]:
        """Get all supported file extensions by type"""
        return {
            "audio": self.audio_extensions,
            "video": self.video_extensions
        }
