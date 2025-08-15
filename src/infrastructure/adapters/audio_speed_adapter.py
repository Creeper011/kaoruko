from pathlib import Path
from typing import Tuple, Optional
from src.domain.ports.speed_service_port import SpeedServicePort
from src.infrastructure.services.speed.audio_speed import AudioSpeedService

class AudioSpeedAdapter(SpeedServicePort):
    def __init__(self):
        self._service = AudioSpeedService()

    def process(
        self,
        input_path: Path,
        output_path: Path,
        speed: float,
        preserve_pitch: bool
    ) -> Tuple[bool, Optional[str], Path]:
        return self._service.process(input_path, output_path, speed, preserve_pitch)
