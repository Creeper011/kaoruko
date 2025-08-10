from abc import ABC, abstractmethod
from pathlib import Path

class BaseSpeedService(ABC):
    """
    Abstract base class for media speed adjustment services.
    
    Subclasses must implement the `process` method to apply speed changes 
    to media files (audio or video).
    """

    @abstractmethod
    def process(self, filepath: Path, output_path: Path, speed_factor: float, preserve_pitch: bool):
        """
        Process the media file to change its playback speed.
        
        Args:
            filepath (Path): Path to the input media file.
            output_path (Path): Path where the processed output file should be saved.
            speed_factor (float): Factor by which to change the playback speed 
                                  (e.g., 1.5 means 1.5x speed).
            preserve_pitch (bool): If the original pitch of the audio should be preserved.
        
        Returns:
            Tuple[bool, Optional[Exception], Path]: 
                - bool indicating success or failure,
                - Exception instance if an error occurred (None if success),
                - Path to the processed output file.
        """
        pass
