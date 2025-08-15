import yt_dlp
import logging
import uuid
import os
import shutil
import asyncio
import glob
from src.config.settings import SettingsManager

logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self, url: str, format: str):
        self.url = url
        self.format = format
        self.loop = None
        self.session_id = str(uuid.uuid4())
        self.settings = SettingsManager()
        self.TEMP_DIR = self.settings.get({"Downloader": "temp_dir"})
        self.CLEAN_UP_TIME = self.settings.get({"Downloader": "cleanup_time"})
        self.temp_dir = self._create_temp_directory()
        self.downloaded_filepath = None
        self._download_task = None
        self.base_yt_dlp_opts = {
            'format': 'best',
            'postprocessors': [],
            'windowsfilenames': True,
            'restrictfilenames': True,
            'outtmpl': os.path.join(self.temp_dir, "%(title)s.%(ext)s"),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'concurrent_fragment_downloads': 10,
            'external_downloader': 'aria2c',
            'external_downloader_args': {
                'default': ['-x', '16', '-s', '16', '-k', '1M']
            },
            'match_filter': yt_dlp.utils.match_filter_func("!is_live"),
        }

    async def __aenter__(self):
        self.loop = asyncio.get_event_loop()
        self._download_task = self.loop.run_in_executor(None, self._download)
        filepath = await self._download_task
        self.downloaded_filepath = filepath
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def _create_temp_directory(self):
        temp_dir = os.path.join(os.getcwd(), self.TEMP_DIR, self.session_id)
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _cleanup(self):
        """Remove temporary files and directories."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {self.temp_dir}: {e}")

    def cancel_download(self):
        """Cancel the download process."""
        try:
            if self._download_task and not self._download_task.done():
                self._download_task.cancel()
                logger.debug("Download task cancelled")
        except Exception as e:
            logger.warning(f"Error cancelling download: {e}")
        
        # Limpar imediatamente
        self._cleanup()

    def _resolve_format(self, format: str):
        match format:
            case "mp4":
                # Try H.264, fallback to bestvideo+bestaudio/best
                fmt = "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
                post = [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mp4"}]
            case "mp3":
                fmt = "bestaudio/best"
                post = [{'key': 'FFmpegExtractAudio', 'preferredcodec': "mp3", 'preferredquality': '0'}]
            case "mkv":
                fmt = "bestvideo+bestaudio/best"
                post = [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "mkv"}]
            case "webm":
                # Try VP9, fallback to bestvideo+bestaudio/best
                fmt = "bestvideo[ext=webm][vcodec=vp9]+bestaudio[ext=webm]/bestvideo+bestaudio/best"
                post = [{'key': 'FFmpegVideoRemuxer', 'preferedformat': "webm"}]
            case "ogg":
                fmt = "bestaudio/best"
                post = [{'key': 'FFmpegExtractAudio', 'preferredcodec': "vorbis", 'preferredquality': '0'}]
            case _:
                logger.error("error: Invalid format specified.")
                raise ValueError("Invalid format specified.")
        return fmt, post

    def _download(self):
        """Video download"""
        try:
            fmt, post = self._resolve_format(self.format)
            opts = self.base_yt_dlp_opts.copy()
            opts.update({'format': fmt, 'postprocessors': post})
            
            logger.debug(f"Downloading with format: {fmt}, postprocessors: {post}")
            logger.debug(f"Temp directory: {self.temp_dir}")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                # Usar template correto com separadores de path
                template = os.path.join(self.temp_dir, "%(title)s.%(ext)s")
                filename = ydl.prepare_filename(info, outtmpl=template)
                logger.debug(f"Expected filename: {filename}")

        except Exception as e:
            logger.warning(f"First download attempt failed: {e}")
            try:
                # tentativa com formato "best"
                opts = self.base_yt_dlp_opts.copy()
                opts.update({'format': 'best', 'postprocessors': []})
                
                logger.debug("Retrying with 'best' format")
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(self.url, download=True)
                    # Usar template correto com separadores de path
                    template = os.path.join(self.temp_dir, "%(title)s.%(ext)s")
                    filename = ydl.prepare_filename(info, outtmpl=template)
                    logger.debug(f"Fallback filename: {filename}")
            except Exception as error:
                logger.error(f"Download failed completely: {error}")
                raise error

        # Resolver o arquivo final baixado
        self.downloaded_filepath = self._resolve_downloaded_file()
        logger.debug(f"Final resolved filepath: {self.downloaded_filepath}")
        
        return self.downloaded_filepath

    def _resolve_downloaded_file(self):
        """Resolve the actual downloaded file from the temp directory"""
        try:
            logger.debug(f"Resolving downloaded file from: {self.temp_dir}")
            
            # Listar todos os arquivos no diretório temporário
            if not os.path.exists(self.temp_dir):
                logger.error(f"Temp directory does not exist: {self.temp_dir}")
                return None
                
            all_files = os.listdir(self.temp_dir)
            logger.debug(f"All items in temp dir: {all_files}")
            
            # Filtrar apenas arquivos (não diretórios)
            files = []
            for item in all_files:
                item_path = os.path.join(self.temp_dir, item)
                if os.path.isfile(item_path):
                    files.append(item_path)
            
            logger.debug(f"Files found: {files}")
            
            if not files:
                logger.error(f"No files found in temp directory: {self.temp_dir}")
                return None
            
            # Primeiro, tentar encontrar arquivos com a extensão esperada
            format_files = [f for f in files if f.lower().endswith(f'.{self.format.lower()}')]
            logger.debug(f"Files with format {self.format}: {format_files}")
            
            if format_files:
                # Ordenar por data de modificação (mais recente primeiro)
                format_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                selected_file = format_files[0]
                logger.debug("Selected file with expected format: {selected_file}")
                return selected_file
            
            # Se não encontrar com a extensão esperada, usar o arquivo mais recente
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            selected_file = files[0]
            logger.debug(f"Selected most recent file: {selected_file}")
            return selected_file
            
        except Exception as e:
            logger.error(f"Error resolving downloaded file: {e}")
            return None

    def get_filepath(self):
        """Returns the filepath"""
        return self.downloaded_filepath