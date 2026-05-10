from typing import Protocol, Dict, Any, runtime_checkable
from pathlib import Path
from logging import Logger

@runtime_checkable
class ConfigLoader(Protocol):
    """Protocol for configuration loaders."""
    def __init__(self, logger: Logger | None = None, config_path: Path | None = None) -> None:
        ...

    def load(self) -> Dict[str, Any]:
        ...
