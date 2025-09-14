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
        logger.debug(f"Getting resolution for file: {filepath}")
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json",
                str(filepath)
            ]
            logger.debug(f"Running ffprobe command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"ffprobe stdout: {result.stdout[:200]}...")
            info = json.loads(result.stdout)

            if not info.get("streams"):
                logger.debug("No video streams found in file")
                return None

            stream = info["streams"][0]
            width = stream.get("width")
            height = stream.get("height")
            resolution = f"{width}x{height}" if width and height else None
            logger.debug(f"Extracted resolution: {resolution}")
            return resolution

        except Exception as e:
            logger.warning(f"Failed to resolve resolution for {filepath}: {e}")
            logger.debug(f"Resolution extraction error details: {type(e).__name__}: {e}")
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
        logger.debug(f"Getting frame rate for file: {filepath}")
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "json",
                str(filepath)
            ]
            logger.debug(f"Running ffprobe command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"ffprobe stdout: {result.stdout[:200]}...")
            info = json.loads(result.stdout)

            if not info.get("streams"):
                logger.debug("No video streams found in file")
                return None

            stream = info["streams"][0]
            fr = stream.get("r_frame_rate")
            logger.debug(f"Raw frame rate from ffprobe: {fr}")
            if fr and fr != "0/0":
                num, den = map(int, fr.split("/"))
                frame_rate = round(num / den, 2)
                logger.debug(f"Calculated frame rate: {frame_rate} fps")
                return frame_rate

            logger.debug("Invalid or zero frame rate")
            return None

        except Exception as e:
            logger.warning(f"Failed to resolve frame rate for {filepath}: {e}")
            logger.debug(f"Frame rate extraction error details: {type(e).__name__}: {e}")
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
        logger.debug(f"Getting file size for: {filepath}")
        try:
            if filepath.exists():
                size = filepath.stat().st_size
                logger.debug(f"File size: {size} bytes ({size / (1024*1024):.2f} MB)")
                return size
            else:
                logger.debug("File does not exist")
                return 0
        except Exception as e:
            logger.warning(f"Failed to get file size for {filepath}: {e}")
            logger.debug(f"File size extraction error details: {type(e).__name__}: {e}")
            return 0
