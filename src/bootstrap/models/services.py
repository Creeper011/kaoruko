from typing import TypedDict
from src.infrastructure.services.config.models.application_settings import DownloadSettings
from src.application.usecases.download_usecase import DownloadUsecase

class Services(TypedDict):
    download_settings: DownloadSettings
    download_usecase: DownloadUsecase