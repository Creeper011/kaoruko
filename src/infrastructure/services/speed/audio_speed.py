import librosa
import soundfile
from mutagen.mp3 import MP3
from pathlib import Path
from .base_speed import BaseSpeedService
from pydub import AudioSegment

class AudioSpeedService(BaseSpeedService):
    def __init__(self):
        super().__init__()

    def _preserve_metadata(self, original_path: Path, output_path: Path) -> bool:
        try:
            original = MP3(str(original_path))
            output = MP3(str(output_path))
            if original.tags:
                output.tags = original.tags
                output.save(v2_version=3)
            return True
        except Exception as e:
            return False

    def process(self, filepath: Path, output_path: Path, speed_factor: float, preserve_pitch: bool):
        if not filepath.exists():
            raise FileExistsError("The file not exists")
        
        output_filename = output_path.parent / f"{output_path.name}"

        success = False
        error = None
        output_file = None

        try:
            match preserve_pitch:
                case True:
                    y, sr = librosa.load(str(filepath))
                    y_changed = librosa.effects.time_stretch(y, rate=speed_factor)
                    soundfile.write(str(output_filename), y_changed, sr)
                case False:
                    audio = AudioSegment.from_file(filepath)
                    new_frame_rate = int(audio.frame_rate * speed_factor)
                    speed_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
                    speed_audio = speed_audio.set_frame_rate(audio.frame_rate)
                    speed_audio.export(output_filename, format=output_path.suffix[1:])

            success = True
            output_file = output_filename
            self._preserve_metadata(filepath, output_file)

        except Exception as exception:
            error = exception

        return (success, error, output_file)