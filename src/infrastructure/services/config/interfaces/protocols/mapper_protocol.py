from typing import Protocol, Any, Dict, runtime_checkable
from src.infrastructure.services.config.models import ApplicationSettings

@runtime_checkable
class MapperProtocol(Protocol):
    """Mapper protocol for mapping system"""

    def can_map(self, data: Dict[str, Any]) -> bool: 
        ...

    def map(self, data: Dict[str, Any], settings: ApplicationSettings) -> ApplicationSettings: 
        ...