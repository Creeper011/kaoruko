import subprocess
from pathlib import Path
from .base_speed import BaseSpeedService

class VideoSpeedService(BaseSpeedService):
    def __init__(self):
        super().__init__()
    
    def process(self, filepath: Path, output_path: Path, speed_factor: float, preserve_pitch: bool):
        if not filepath.exists():
            raise FileNotFoundError("The file does not exist")
        
        pts_factor = 1.0 / speed_factor
        
        match preserve_pitch:
            case True:
                cmd = [
                    'ffmpeg', '-i', str(filepath),
                    '-filter:v', f'setpts={pts_factor}*PTS',
                    '-filter:a', f'atempo={speed_factor}',
                    '-y', str(output_path)
                ]
            case False:
                rate_factor = speed_factor
                cmd = [
                    'ffmpeg', '-i', str(filepath),
                    '-filter_complex', 
                    f'[0:v]setpts={pts_factor}*PTS[v];[0:a]asetrate=44100*{rate_factor},aresample=44100[a]',
                    '-map', '[v]', '-map', '[a]',
                    '-y', str(output_path)
                ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return (True, None, output_path)
        except subprocess.CalledProcessError as e:
            return (False, e.stderr, None)
        except FileNotFoundError:
            return (False, "FFmpeg not found", None)