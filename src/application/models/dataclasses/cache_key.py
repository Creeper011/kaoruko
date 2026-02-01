
from dataclasses import dataclass
from src.domain.enum.formats import Formats
from src.domain.enum.quality import Quality

@dataclass(frozen=True)
class CacheKey():
    """Unique identifier for cached items based on URL, format, and quality."""
    url: str
    format_value: Formats
    quality: Quality | None = None