from src.domain.usecases import (
    DownloadUsecase,
    ExtractAudioUsecase
)
from src.infrastructure.orchestrators import (
    DownloadOrchestrator,
)
from src.infrastructure.services import (
    AudioExtractService,
)

class BuilderMan():
    """Manages building processes for usecases"""

    @staticmethod
    def build_download_usecase() -> DownloadUsecase:
        return DownloadUsecase(DownloadOrchestrator)

    @staticmethod
    def build_extract_audio_usecase() -> ExtractAudioUsecase:
        return ExtractAudioUsecase(AudioExtractService)