from pathlib import Path
from abc import ABC, abstractmethod

class BaseCrusherService(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def process(self, input_file: Path, output_path: Path) -> None:
        pass
