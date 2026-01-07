from typing import TypedDict
from src.infrastructure.services.config.models.application_settings import DownloadSettings
from src.application.usecases.download_usecase import DownloadUsecase

class Services(TypedDict):
    DownloadUsecase: DownloadUsecase