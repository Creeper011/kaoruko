import logging
from pathlib import Path
from typing import Dict, Any, Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TRCK, TDRC

logger = logging.getLogger(__name__)

class MetadataEmbedderService:
    """
    A service to embed metadata into MP3 files.
    """

    async def apply_metadata(self, file_path: Path, metadata: Dict[str, Any], image_cover_art: Optional[bytes]):
        """
        Applies metadata and cover art to an MP3 file.

        Args:
            file_path: The path to the MP3 file.
            metadata: A dictionary of metadata tags.
            image_cover_art: The cover art image in bytes.
        """
        try:
            logger.debug(f"Applying metadata to file: {file_path}")
            audio = MP3(file_path, ID3=ID3)

            # Add new tags
            if 'title' in metadata:
                audio.tags.add(TIT2(encoding=3, text=metadata['title']))
            if 'artist' in metadata:
                audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
            if 'album' in metadata:
                audio.tags.add(TALB(encoding=3, text=metadata['album']))
            if 'track_number' in metadata:
                audio.tags.add(TRCK(encoding=3, text=str(metadata['track_number'])))
            if 'release_date' in metadata:
                audio.tags.add(TDRC(encoding=3, text=metadata['release_date']))

            if image_cover_art:
                audio.tags.add(
                    APIC(
                        encoding=3,  # 3 is for utf-8
                        mime='image/jpeg',  # image/png...
                        type=3,  # 3 is for the cover image
                        desc='Cover',
                        data=image_cover_art
                    )
                )
            
            audio.save()
            logger.info(f"Metadata successfully applied to {file_path.name}")

        except Exception as e:
            logger.error(f"Failed to apply metadata to {file_path.name}: {e}", exc_info=True)
