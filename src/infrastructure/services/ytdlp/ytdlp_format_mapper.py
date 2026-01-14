import logging
from logging import Logger
from typing import Optional
from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality

class YtdlpFormatMapper():
    """Mapper the format string to yt-dlp format codes.

    Example:
        'mp4' -> 'bestvideo/best'
        'worst' -> 'worstaudio/worst'
    """

    FORMAT_MAP: dict[str, dict] = {
            "mp4": {
                "format": "bestvideo[vcodec=avc1][ext=mp4]+bestaudio/bestvideo[vcodec=avc1]+bestaudio/bestvideo[ext=mp4]+bestaudio/bestvideo+bestaudio/bestvideo+bestaudio/best",
                "post": [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mp4"}],
                "is_audio": False
            },
            "mp3": {
                "format": "bestaudio/bestaudio",
                "post": [{'key': 'FFmpegExtractAudio', 'preferredcodec': "mp3", 'preferredquality': '0'}],
                "is_audio": True
            },
            "mkv": {
                "format": "bestvideo+bestaudio",
                "post": [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mkv"}],
                "is_audio": False
            },
            "webm": {
                "format": "bestvideo[ext=webm]+bestaudio[ext=webm]/bestvideo+bestaudio",
                "post": [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "webm"}],
                "is_audio": False
            },
            "ogg": {
                "format": "bestaudio/bestaudio",
                "post": [{'key': 'FFmpegExtractAudio', 'preferredcodec': "vorbis", 'preferredquality': '0'}],
                "is_audio": True
            }
        }

    @classmethod
    def map_format(cls, format_value: Formats | None, quality: Quality | None = None, logger: Optional[Logger] = None) -> dict:
        """Map the format string to yt-dlp format codes.

        Args:
            format_value: Format enum provided by the user
            quality: Quality enum for video resolution
            logger: Logger instance for logging messages
        Returns:
            yt-dlp format options dictionary

        Raises:
            ValueError: If the format string is not recognized
        """
        if logger is None:
            logger = logging.getLogger(cls.__name__)

        if format_value is None:
            return {
                "format": "bestvideo+bestaudio/best"
            }

        format_info = cls.FORMAT_MAP.get(format_value.value)
        if not format_info:
            logger.error(f"Unrecognized format: {format_value}")
            raise ValueError(f"Unrecognized format: {format_value}")

        if quality and not format_info.get("is_audio", False):
            height = cls._get_height_from_quality(quality)
            format_info = format_info.copy()
            format_info["format"] = cls._apply_quality_filter(format_info["format"], height)

        logger.debug(f"Mapped format '{format_value.value}' with quality '{quality}' to yt-dlp format options: {format_info}")
        return format_info

    @classmethod
    def _get_height_from_quality(cls, quality: Quality) -> int:
        """Extract height from quality enum value."""
        return int(quality.value[:-1]) 

    @classmethod
    def _apply_quality_filter(cls, format_str: str, height: int) -> str:
        """Apply height filter to video streams only.
        
        The height filter should only be applied to bestvideo/video streams,
        not to bestaudio/audio streams.
        """
        format_options = format_str.split('/')
        filtered_options = []
        
        for option in format_options:
            if not option.strip():
                continue
                
            # Split by '+' to handle combined streams (bestvideo+bestaudio)
            streams = option.split('+')
            filtered_streams = []
            
            for stream in streams:
                # Apply height filter only to video streams
                if 'bestvideo' in stream or 'video' in stream or stream.startswith('best['):
                    # Add height filter to video selector
                    filtered_streams.append(f"{stream}[height<={height}]")
                else:
                    # Leave audio streams and other selectors unchanged
                    filtered_streams.append(stream)
            
            filtered_options.append('+'.join(filtered_streams))
        
        return '/'.join(filtered_options)