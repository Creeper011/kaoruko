from logging import Logger
from src.domain.enum.formats import Formats

class YtdlpFormatMapper():
    """Mapper the format string to yt-dlp format codes.

    Example:
        'mp4' -> 'bestvideo/best'
        'worst' -> 'worstaudio/worst'
    """

    FORMAT_MAP: dict[str, dict] = {
            "mp4": {
                "format": "bestvideo[vcodec=avc1][ext=mp4]+bestaudio/bestvideo[vcodec=avc1]{video_quality}+bestaudio{audio_quality}/bestvideo{video_quality}[ext=mp4]+bestaudio{audio_quality}/bestvideo{video_quality}+bestaudio{audio_quality}/bestvideo+bestaudio/best",
                "post": [{'key': 'FFmpegVideoConvertor', 'preferedformat': "mp4"}], # if should_transcode else {'key': 'FFmpegVideoRemuxer', 'preferedformat': "mp4"}],
                "is_audio": False
            },
            "mp3": {
                "format": "bestaudio/bestaudio",
                "post": [{'key': 'FFmpegExtractAudio', 'preferredcodec': "mp3", 'preferredquality': '0'}],
                "is_audio": True
            },
            "mkv": {
                "format": "bestvideo+bestaudio",
                "post": [{'key': 'FFmpegVideoConvertor', 'preferedformat': "mkv"}], #if should_transcode else {'key': 'FFmpegVideoRemuxer', 'preferedformat': "mkv"}],
                "is_audio": False
            },
            "webm": {
                "format": "bestvideo[ext=webm]+bestaudio[ext=webm]/bestvideo+bestaudio",
                "post": [{'key': 'FFmpegVideoConvertor', 'preferedformat': "webm"}], #    if should_transcode else {'key': 'FFmpegVideoRemuxer', 'preferedformat': "webm"}],
                "is_audio": False
            },
            "ogg": {
                "format": "bestaudio/bestaudio",
                "post": [{'key': 'FFmpegExtractAudio', 'preferredcodec': "vorbis", 'preferredquality': '0'}],
                "is_audio": True
            }
        }

    @classmethod
    def map_format(cls, format_value: Formats | None, logger: Logger) -> dict:
        """Map the format string to yt-dlp format codes.

        Args:
            format: Format string provided by the user
            logger: Logger instance for logging messages
        Returns:
            yt-dlp format options dictionary

        Raises:
            ValueError: If the format string is not recognized
        """
        if format_value is None:
            return {
                "format": "bestvideo+bestaudio/best"
            }

        format_info = cls.FORMAT_MAP.get(format_value.value)
        if not format_info:
            logger.error(f"Unrecognized format: {format_value}")
            raise ValueError(f"Unrecognized format: {format_value}")

        logger.debug(f"Mapped format '{format_value.value}' to yt-dlp format options: {format_info}")
        return format_info