from abc import ABC, abstractmethod

class Compositor(ABC):
    """Define basic model for a compositor"""

    @abstractmethod
    def compose(self) -> None:
        """Compose/wire a module"""
        ...