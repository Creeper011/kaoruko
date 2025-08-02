from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Result:
    ok: bool
    value: Optional[Any] = None
    error: Optional[str] = None
    type: Optional[str] = None

    @classmethod
    def success(cls, value=None):
        return cls(ok=True, value=value)

    @classmethod
    def failure(cls, error, type=None):
        return cls(ok=False, error=error, type=type)