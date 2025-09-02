import logging
from typing import Optional
from src.infrastructure.services.drive import Drive
from src.infrastructure.services.base_drive_loader import BaseDriveLoader
from src.application.config import SettingsManager

logger = logging.getLogger(__name__)

class DriveLoader(BaseDriveLoader):
    """Concrete implementation of Drive dependency loader for dependency injection"""
    
    def __init__(self):
        self._drive_instance: Optional[Drive] = None
        self._settings = SettingsManager()
    
    def load_drive(self, folder: Optional[str] = None) -> Drive:
        """
        Loads and returns a Drive instance with proper configuration.
        
        Args:
            folder (str): Optional folder name for the Drive instance
            
        Returns:
            Drive: Configured Drive instance
        """
        if self._drive_instance is None:
            try:
                # Get folder from settings if not provided
                if folder is None:
                    folder = self._settings.get({'Drive': 'default_folder'}) or "default"
                
                # Get drive_path from settings
                drive_path = self._settings.get({'Drive': 'DrivePath'})
                if not drive_path:
                    raise RuntimeError("DrivePath not configured in settings")
                
                self._drive_instance = Drive(folder, drive_path)
                logger.debug(f"Drive instance loaded successfully with folder: {folder}")
                
            except Exception as e:
                logger.error(f"Failed to load Drive instance: {e}")
                raise RuntimeError(f"Drive initialization failed: {e}")
        
        return self._drive_instance
    
    def get_drive(self) -> Drive:
        """
        Returns the current Drive instance.
        Creates one if it doesn't exist.
        
        Returns:
            Drive: Current Drive instance
        """
        if self._drive_instance is None:
            return self.load_drive()
        return self._drive_instance
    
    def reset_drive(self) -> None:
        """Resets the Drive instance (useful for testing or reconfiguration)"""
        self._drive_instance = None
        logger.info("Drive instance reset")

