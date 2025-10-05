import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional

class EnvSettings:
    """
    Manages loading environment variables from a .env file and provides specific getters.
    """

    @staticmethod
    def load_env(env_path: Path = Path(".env")) -> bool:
        """
        Loads environment variables from a .env file using dotenv.
        
        Args:
            env_path (Path): Path to the .env file. Defaults to Path(".env")
            
        Returns:
            bool: True if .env file was loaded successfully, False otherwise
            
        Raises:
            FileNotFoundError: If the .env file doesn't exist
        """
        env_path = Path(env_path)
        
        if not env_path.exists():
            raise FileNotFoundError(f"Environment file not found: {env_path}")
        
        loaded_env = load_dotenv(env_path)
        
        if not loaded_env:
            raise RuntimeError(f"Failed to load environment file: {env_path}")
        
        return loaded_env

    @staticmethod
    def get_spotify_settings() -> Optional[Dict[str, str]]:
        """
        Retrieves Spotify credentials from environment variables.

        Returns:
            A dictionary with client_id and client_secret, or None if not set.
        """
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

        if client_id and client_secret:
            return {"client_id": client_id, "client_secret": client_secret}
        
        return None
