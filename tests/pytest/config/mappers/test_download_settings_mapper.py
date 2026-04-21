from src.domain.models.settings.download_settings import (
    DEFAULT_DOWNLOAD_API_BASE_URL,
    DEFAULT_DOWNLOAD_API_POLL_INTERVAL_SECONDS,
    DEFAULT_DOWNLOAD_API_TIMEOUT_SECONDS,
)
from src.infrastructure.services.config.mappers.modules.download_settings_mapper import DownloadSettingsMapper
from src.infrastructure.services.config.models import ApplicationSettings


def test_download_settings_mapper_maps_api_fields() -> None:
    mapper = DownloadSettingsMapper()
    data = {
        "download": {
            "file_size_limit": 123,
            "blacklist_sites": ["example.com"],
            "api_base_url": "http://api.internal:8000",
            "api_poll_interval_seconds": 0.25,
            "api_timeout_seconds": 321.0,
        }
    }

    settings = mapper.map(data, ApplicationSettings())

    assert settings.download_settings is not None
    assert settings.download_settings.file_size_limit == 123
    assert settings.download_settings.blacklist_sites == ["example.com"]
    assert settings.download_settings.api_base_url == "http://api.internal:8000"
    assert settings.download_settings.api_poll_interval_seconds == 0.25
    assert settings.download_settings.api_timeout_seconds == 321.0


def test_download_settings_mapper_uses_api_defaults() -> None:
    mapper = DownloadSettingsMapper()

    settings = mapper.map({"download": {}}, ApplicationSettings())

    assert settings.download_settings is not None
    assert settings.download_settings.api_base_url == DEFAULT_DOWNLOAD_API_BASE_URL
    assert settings.download_settings.api_poll_interval_seconds == DEFAULT_DOWNLOAD_API_POLL_INTERVAL_SECONDS
    assert settings.download_settings.api_timeout_seconds == DEFAULT_DOWNLOAD_API_TIMEOUT_SECONDS
