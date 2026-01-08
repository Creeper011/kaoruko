"""This module defines all default costants.. normaly used as fallback values."""

from pathlib import Path
from yt_dlp.utils import match_filter_func

DEFAULT_YAML_CONFIG_PATH = Path("config.yaml")
YAML_FILE_ENCODING = "UTF-8"
DEFAULT_ENV_CONFIG_PATH = Path(".env")
DEFAULT_LOADERS_PATH = Path("src/infrastructure/services/config/loaders")
DEFAULT_COMMANDS_PATH = Path("src/presentation/discord/commands")
DEFAULT_DISCORD_RECONNECT = True
DEFAULT_DEBUG_FLAG = ("-d", "--debug")
CACHE_DIR = Path(".cache")
CACHE_INDEX_FILE = CACHE_DIR / "index.json"
DEFAULT_TEMP_DIR = Path(".temp")
DRIVE_MAX_RETRY_COUNT = 3
DEFAULT_YT_DLP_SETTINGS = {
    'js_runtimes': {
        'node': {}
    },
    'remote_components': ['ejs:github'],
    'postprocessors': [],
    'noplaylist': True,
    'no_warnings': True,
    'concurrent_fragment_downloads': 10,
    'continue_dl': True,
    'external_downloader': 'aria2c',
    'external_downloader_args': {'default': ['-x', '16', '-s', '16', '-k', '1M']},
    'match_filter': match_filter_func("!is_live"),
}
DRIVE_BASE_FILE_UPLOAD_URL = "https://drive.google.com/file/d/"
DEFAULT_DOWNLOAD_FORMAT = "mp4" # change this later to a better method