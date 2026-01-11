from abc import ABC, abstractmethod
from typing import Any

class Builder(ABC):
    """Define basic model for a builder"""

    @abstractmethod
    def build(self) -> Any:
        """Build an object to application"""
        ...