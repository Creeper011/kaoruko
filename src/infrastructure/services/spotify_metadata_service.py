import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
import httpx
from typing import Optional, Tuple, Dict, Any
from src.application.config.env_settings import EnvSettings

logger = logging.getLogger(__name__)

class SpotifyMetadataService:
    """
    A service to fetch track metadata from Spotify.
    """
    _spotify_client: Optional[spotipy.Spotify] = None

    def __init__(self):
        spotify_creds = EnvSettings.get_spotify_settings()
        if spotify_creds:
            self.client_id = spotify_creds.get('client_id')
            self.client_secret = spotify_creds.get('client_secret')
        else:
            self.client_id = None
            self.client_secret = None

    def _login(self):
        """
        Initializes the Spotipy client if it hasn't been already.
        The login is lazy and only happens on the first call.
        """
        if self.__class__._spotify_client is None:
            if not self.client_id or not self.client_secret:
                logger.warning("Spotify credentials (SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET) are not set. Cannot fetch metadata.")
                return

            try:
                logger.debug("Initializing Spotify client...")
                auth_manager = SpotifyClientCredentials(client_id=self.client_id, client_secret=self.client_secret)
                self.__class__._spotify_client = spotipy.Spotify(auth_manager=auth_manager)
                logger.info("Spotify client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}", exc_info=True)
                self.__class__._spotify_client = None


    async def fetch_track(self, track_name: str) -> Optional[Tuple[Dict[str, Any], bytes]]:
        """
        Fetches track metadata and cover art from Spotify.

        Args:
            track_name: The name of the track to search for.

        Returns:
            A tuple containing a dictionary of metadata and the cover art in bytes, or None if not found.
        """
        self._login()
        if self.__class__._spotify_client is None:
            return None

        try:
            logger.debug(f"Searching Spotify for track: {track_name}")
            results = self.__class__._spotify_client.search(q=track_name, type='track', limit=1)
            
            if not results or not results['tracks']['items']:
                logger.warning(f"No track found on Spotify for query: {track_name}")
                return None

            track = results['tracks']['items'][0]
            album_cover_url = track['album']['images'][0]['url'] if track['album']['images'] else None

            metadata = {
                'title': track['name'],
                'artist': ', '.join(artist['name'] for artist in track['artists']),
                'album': track['album']['name'],
                'track_number': track['track_number'],
                'release_date': track['album']['release_date'],
            }
            logger.info(f"Found track: {metadata['title']} - {metadata['artist']}")

            image_bytes = None
            if album_cover_url:
                async with httpx.AsyncClient() as client:
                    logger.debug(f"Downloading cover art from: {album_cover_url}")
                    response = await client.get(album_cover_url)
                    response.raise_for_status()
                    image_bytes = response.content
                    logger.debug("Cover art downloaded successfully.")

            return metadata, image_bytes

        except Exception as e:
            logger.error(f"An error occurred while fetching from Spotify: {e}", exc_info=True)
            return None
