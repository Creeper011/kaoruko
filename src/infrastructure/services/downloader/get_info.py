import json
import subprocess
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MediaInfoExtractor:
    """
    Extracts media information (resolution, frame rate) from downloaded files using ffprobe.
    """

    @staticmethod
    def get_resolution(filepath: Path) -> Optional[str]:
        """
        Retrieve the video resolution from the given file using ffprobe.

        Args:
            filepath (Path): Path to the media file.

        Returns:
            Optional[str]: Resolution in the format "widthxheight" (e.g., "1920x1080"),
                        or None if unavailable or not a video file.
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json",
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            if not info.get("streams"):
                return None

            stream = info["streams"][0]
            width = stream.get("width")
            height = stream.get("height")
            return f"{width}x{height}" if width and height else None

        except Exception as e:
            logger.warning(f"Failed to resolve resolution for {filepath}: {e}")
            return None

    @staticmethod
    def get_frame_rate(filepath: Path) -> Optional[float]:
        """
        Retrieve the frame rate (fps) from the given file using ffprobe.

        Args:
            filepath (Path): Path to the media file.

        Returns:
            Optional[float]: Frame rate as a float (rounded to 2 decimals),
                            or None if unavailable or not a video file.
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "json",
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            if not info.get("streams"):
                return None

            stream = info["streams"][0]
            fr = stream.get("r_frame_rate")
            if fr and fr != "0/0":
                num, den = map(int, fr.split("/"))
                return round(num / den, 2)

            return None

        except Exception as e:
            logger.warning(f"Failed to resolve frame rate for {filepath}: {e}")
            return None

    @staticmethod
    def get_file_size(filepath: Path) -> int:
        """
        Get the file size in bytes.

        Args:
            filepath (Path): Path to the file.

        Returns:
            int: File size in bytes, or 0 if file doesn't exist.
        """
        try:
            return filepath.stat().st_size if filepath.exists() else 0
        except Exception as e:
            logger.warning(f"Failed to get file size for {filepath}: {e}")
            return 0

    @staticmethod
    def get_file_size_mb(filepath: Path) -> float:
        """
        Get the file size in megabytes.

        Args:
            filepath (Path): Path to the file.

        Returns:
            float: File size in MB (rounded to 2 decimals).
        """
        size_bytes = MediaInfoExtractor.get_file_size(filepath)
        return round(size_bytes / (1024 * 1024), 2)
