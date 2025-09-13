from src.domain.usecases import (
    DownloadUsecase,
#    BitCrusherUsecase,
#    SpeedMedia,
#    MediaAudioExtractor
)
from src.infrastructure.orchestrators.downloader import DownloadOrchestrator

class BuilderMan():
    """Manages building processes for usecases"""

    @staticmethod
    def build_download_usecase() -> DownloadUsecase:
        return DownloadUsecase(DownloadOrchestrator)

#   @staticmethod
#    def build_bit_crusher_usecase() -> BitCrusherUsecase:
#        return BitCrusherUsecase(AudioCrusher())

#    @staticmethod
#    def build_speed_media_usecase() -> SpeedMedia:
#        return SpeedMedia(AudioSpeedService(), VideoSpeedService())

#    @staticmethod
#    def build_media_audio_extractor() -> MediaAudioExtractor:
#        return MediaAudioExtractor()