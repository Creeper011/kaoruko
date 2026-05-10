from src.services.config.loaders import YumlyLoader
from src.services.config.models import ApplicationSettings
from src.services.config.settings_factory import SettingsFactory


def build_settings() -> ApplicationSettings:
    """Builds application settings."""
    loaders = {YumlyLoader()}
    settings_factory = SettingsFactory(logger=None, loaders=loaders)
    return settings_factory.build_settings()
