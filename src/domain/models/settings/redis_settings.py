
from dataclasses import dataclass

@dataclass(frozen=True)
class RedisSettings:
    host: str 
    port: int
    username: str | None = None
    password: str | None = None