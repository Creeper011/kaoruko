from dataclasses import dataclass, field
from typing import List, Optional
from discord import Intents

@dataclass(frozen=True)
class DiscordSettings:
    token: Optional[str] = None
    prefix: List[str] = field(default_factory=lambda: ["*"])
    owner_id: int = 0
    intents: Optional[Intents] = None
