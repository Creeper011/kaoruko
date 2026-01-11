import logging
import dataclasses
from typing import Dict, Any, Optional
from logging import Logger
from src.domain.models.settings import RedisSettings
from src.core.constants import DEFAULT_REDIS_HOST, DEFAULT_REDIS_PORT, DEFAULT_REDIS_USERNAME, DEFAULT_REDIS_PASSWORD
from src.infrastructure.services.config.models import ApplicationSettings
from src.infrastructure.services.config.interfaces.protocols import MapperProtocol

class RedisSettingsMapper(MapperProtocol):
    """Maps redis settings into ApplicationSettings.redis_settings"""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def can_map(self, data: Dict[str, Any]) -> bool:
        return "redis" in data

    def map(self, data: Dict[str, Any], settings: ApplicationSettings) -> ApplicationSettings:
        try:
            self.logger.debug(f"Mapping Redis settings from data: {data}")
            redis_config: Dict[str, Any] = data.get("redis", {})

            redis_settings = RedisSettings(
                host=redis_config.get("host", DEFAULT_REDIS_HOST),
                port=redis_config.get("port", DEFAULT_REDIS_PORT),
                username=redis_config.get("username", DEFAULT_REDIS_USERNAME),
                password=redis_config.get("password", DEFAULT_REDIS_PASSWORD),
            )

            new_settings = dataclasses.replace(settings, redis_settings=redis_settings)
            self.logger.debug("Redis settings mapped and attached to ApplicationSettings")
            return new_settings
        except Exception as exc:
            self.logger.error(f"Failed to map Redis settings: {exc}")
            raise