import logging
from typing import Optional
from src.infrastructure.services.drive.drive import Drive
from src.infrastructure.services.drive.base_drive_loader import BaseDriveLoader
from src.application.config import SettingsManager

logger = logging.getLogger(__name__)

class DriveLoader(BaseDriveLoader):
    """Concrete implementation of Drive dependency loader for dependency injection"""
    
    def __init__(self):
        logger.debug("Initializing DriveLoader")
        self._drive_instance: Optional[Drive] = None
        self._settings = SettingsManager()
        logger.debug("DriveLoader initialized successfully")
    
    def load_drive(self, folder: Optional[str] = None) -> Drive:
        """
        Loads and returns a Drive instance with proper configuration.
        
        Args:
            folder (str): Optional folder name for the Drive instance
            
        Returns:
            Drive: Configured Drive instance
        """
        logger.debug(f"Loading Drive instance with folder: {folder}")
        if self._drive_instance is None:
            try:
                # Get folder from settings if not provided
                if folder is None:
                    folder = self._settings.get({'Drive': 'default_folder'}) or "default"
                    logger.debug(f"Using default folder from settings: {folder}")
                
                # Get drive_path from settings
                drive_path = self._settings.get({'Drive': 'DrivePath'})
                logger.debug(f"Retrieved drive_path from settings: {drive_path}")
                if not drive_path:
                    logger.error("DrivePath not configured in settings")
                    raise RuntimeError("DrivePath not configured in settings")
                
                logger.debug(f"Creating Drive instance with folder='{folder}', drive_path='{drive_path}'")
                self._drive_instance = Drive(folder, drive_path)
                logger.debug(f"Drive instance loaded successfully with folder: {folder}")
                
            except Exception as e:
                logger.error(f"Failed to load Drive instance: {e}")
                logger.debug(f"Drive loading error details: {type(e).__name__}: {e}")
                raise RuntimeError(f"Drive initialization failed: {e}")
        else:
            logger.debug("Using existing Drive instance")
        
        return self._drive_instance
    
    def get_drive(self) -> Drive:
        """
        Returns the current Drive instance.
        Creates one if it doesn't exist.
        
        Returns:
            Drive: Current Drive instance
        """
        logger.debug("Getting Drive instance")
        if self._drive_instance is None:
            logger.debug("No existing Drive instance, loading new one")
            return self.load_drive()
        logger.debug("Returning existing Drive instance")
        return self._drive_instance
    
    def reset_drive(self) -> None:
        """Resets the Drive instance (useful for testing or reconfiguration)"""
        logger.debug("Resetting Drive instance")
        self._drive_instance = None
        logger.info("Drive instance reset")
        logger.debug("Drive instance reset completed")

