import numpy
import soundfile
from pathlib import Path
from mutagen.mp3 import MP3
from src.infrastructure.services.bitcrusher.basecrusherService import BaseCrusherService

class AudioCrusher(BaseCrusherService):
    def __init__(self, bit_depth: int, downsample_rate: int):
        self.bit_depth = bit_depth
        self.downsample_rate = downsample_rate
        self.valid_rates = [8000, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000]

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
        
    def process(self, input_file: Path, output_path: Path) -> None:
        audio, source_rate = soundfile.read(str(input_file))

        target_rate = min(self.valid_rates, key=lambda r: abs(r - self.downsample_rate))

        factor = source_rate / target_rate
        indices = (numpy.arange(0, len(audio), factor)).astype(int)
        indices = indices[indices < len(audio)] 
        audio_resampled = audio[indices]

        max_val = numpy.max(numpy.abs(audio_resampled))
        if max_val == 0:
            max_val = 1.0
        audio_norm = audio_resampled / max_val
        audio_bits = numpy.round(audio_norm * (2**(self.bit_depth - 1))) / (2**(self.bit_depth - 1))
        audio_out = audio_bits * max_val

        soundfile.write(str(output_path), audio_out, target_rate, format='MP3')
        self._preserve_metadata(input_file, output_path)
