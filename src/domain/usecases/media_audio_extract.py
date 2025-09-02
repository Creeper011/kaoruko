from pathlib import Path
import discord
from src.domain.services.media_validation import MediaValidationService

class MediaAudioExtractor():
    def __init__(self):
        self.media_validator = MediaValidationService()
    
    def _verify_mimetype(self, file_path: Path) -> bool:
        """Verify if the file is a valid media file using domain validation service"""
        is_valid, _ = self.media_validator.validate_media_file(file_path)
        return is_valid

    def extract_audio_from_attachment(self, attachment: discord.Attachment):
        file_path = Path(attachment.filename)
        if not self._verify_mimetype(file_path):
            raise ValueError("Invalid media file format")
        # Implement audio extraction logic
        pass

    def extract_audio(self, file_path: Path):
        if not self._verify_mimetype(file_path):
            raise ValueError("Invalid media file format")
        # Implement audio extraction logic
        pass
