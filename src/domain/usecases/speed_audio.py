import librosa
import soundfile
import time
import asyncio
import os
import uuid
import shutil
from pathlib import Path
from pydub import AudioSegment
from mutagen import File
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from src.domain.entities import SpeedAudioResult
from src.infrastructure.services.drive import Drive

class SpeedControlAudio():
    def __init__(self):
        self.FILE_SIZE_LIMIT = 120 * 1024 * 1024  # 120 MB
        self.drive = Drive("")

    def _create_temp_dir(self) -> Path:
        """Create a temporary directory for processing"""
        temp_dir = Path("temp/speed_control")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        unique_id = str(uuid.uuid4())
        temp_dir = temp_dir / unique_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        return temp_dir

    def _cleanup_temp_dir(self, temp_dir: Path):
        """Clean up temporary directory and files"""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")

    def _preserve_metadata(self, original_path: Path, output_path: Path):
        """Preserva os metadados ID3 do arquivo original para o arquivo de saída usando mutagen.MP3"""
        try:
            original = MP3(original_path)
            output = MP3(output_path)
            if original.tags:
                output.tags = original.tags
                output.save(v2_version=3) 
        except Exception as e:
            pass

    def change_speed(self, factor: float, preserve_pitch: bool, filepath: Path) -> SpeedAudioResult:
        if not filepath.exists():
            raise FileNotFoundError("File not exists")

        start = time.time()
        temp_dir = None

        try:
            base_name = filepath.name
            filename = f"{factor}x - {base_name}"
            output_path = filepath.parent / filename
            
            if preserve_pitch:
                y, sr = librosa.load(filepath, sr=None)
                y_stretched = librosa.effects.time_stretch(y, rate=factor)
                
                soundfile.write(output_path, y_stretched, sr, format='MP3')
                
                self._preserve_metadata(filepath, output_path)
            else:
                audio = AudioSegment.from_file(filepath)
                new_audio = audio._spawn(
                    audio.raw_data, 
                    overrides={"frame_rate": int(audio.frame_rate * factor)}
                )
                new_audio = new_audio.set_frame_rate(audio.frame_rate)
                new_audio.export(output_path, format="mp3")
                
                self._preserve_metadata(filepath, output_path)

            elapsed = time.time() - start
            
            # Check file size
            file_size = os.path.getsize(output_path)
            drive_link = None
            
            if file_size > self.FILE_SIZE_LIMIT:
                # Upload to Drive if file is too large
                drive_link = self.drive.uploadToDrive(output_path)
                # Clean up local file after upload
                if output_path.exists():
                    output_path.unlink()
                output_path = None
            
            result = SpeedAudioResult(
                factor=factor, 
                filepath=output_path, 
                elapsed=elapsed,
                file_size=file_size,
                drive_link=drive_link
            )
            return result

        except Exception as e:
            # Clean up on error
            if temp_dir and temp_dir.exists():
                self._cleanup_temp_dir(temp_dir)
            raise e

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

    def process_with_temp_dir(self, factor: float, preserve_pitch: bool, input_path: Path) -> SpeedAudioResult:
        """Process audio with temporary directory management"""
        temp_dir = self._create_temp_dir()
        
        try:
            # Copy input file to temp directory
            temp_input_path = temp_dir / input_path.name
            shutil.copy2(input_path, temp_input_path)
            
            # Process the audio
            result = self.change_speed(factor, preserve_pitch, temp_input_path)
            
            # If result has a filepath, move it to temp_dir for cleanup
            if result.filepath and result.filepath.exists():
                temp_output_path = temp_dir / result.filepath.name
                shutil.move(result.filepath, temp_output_path)
                result.filepath = temp_output_path
            
            return result
            
        except Exception as e:
            self._cleanup_temp_dir(temp_dir)
            raise e