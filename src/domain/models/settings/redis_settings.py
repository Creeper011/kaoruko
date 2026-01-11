
from dataclasses import dataclass

@dataclass(frozen=True)
class RedisSettings:
    host: str 
    port: int
    cache_db: int
    login_db: int
    username: str | None = None
    password: str | None = None