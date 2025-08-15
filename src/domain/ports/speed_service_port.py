from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Optional

class SpeedServicePort(ABC):
    @abstractmethod
    def process(
        self,
        input_path: Path,
        output_path: Path,
        speed: float,
        preserve_pitch: bool
    ) -> Tuple[bool, Optional[str], Path]:
        ...
