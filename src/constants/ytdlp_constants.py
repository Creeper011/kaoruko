from yt_dlp.utils import match_filter_func

DEFAULT_YT_DLP_SETTINGS = {
    'js_runtimes': {
        'node': {}
    },
    'cookiefile': 'cookies.txt',
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
DEFAULT_DOWNLOAD_FORMAT = "mp4" # change this later to a better method
DEFAULT_DOWNLOAD_FILESIZE_LIMIT = 25 * 1024 * 1024