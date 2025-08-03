import librosa
import soundfile
import time
import asyncio
from pathlib import Path
from pydub import AudioSegment
from src.domain.entities import SpeedAudioResult

class SpeedControlAudio():
    def __init__(self):
        pass

    def change_speed(self, factor: float, preserve_pitch: bool, filepath: Path) -> SpeedAudioResult:
        if not filepath.exists():
            raise FileNotFoundError("File not exists")

        start = time.time()

        base_name = filepath.name
        filename = f"{factor}x - {base_name}"
        output_path = filepath.parent / filename
        
        if preserve_pitch:
            y, sr = librosa.load(filepath, sr=None)
            y_stretched = librosa.effects.time_stretch(y, rate=factor)
            soundfile.write(output_path, y_stretched, sr, format='MP3')
        else:
            audio = AudioSegment.from_file(filepath)
            new_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * factor)})
            new_audio = new_audio.set_frame_rate(audio.frame_rate)
            new_audio.export(output_path, format="mp3")

        elapsed = time.time() - start
        result = SpeedAudioResult(factor=factor, filepath=output_path, elapsed=elapsed)
        return result

    async def change_speed_async(self, factor: float, preserve_pitch: bool, filepath: Path) -> SpeedAudioResult:
        """Async version that runs the processing in a thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.change_speed, 
            factor, 
            preserve_pitch, 
            filepath
        )