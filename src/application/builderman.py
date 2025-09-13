from src.domain.usecases import (
    DownloadUsecase,
#    BitCrusherUsecase,
#    SpeedMedia,
#    MediaAudioExtractor
)
from src.infrastructure.services import (
    Downloader,
#    AudioCrusher,
#    AudioSpeedService,
#    VideoSpeedService,
)

class BuilderMan():
    """Manages building processes for usecases"""

    @staticmethod
    def build_download_usecase() -> DownloadUsecase:
        return DownloadUsecase(Downloader)

#   @staticmethod
#    def build_bit_crusher_usecase() -> BitCrusherUsecase:
#        return BitCrusherUsecase(AudioCrusher())

#    @staticmethod
#    def build_speed_media_usecase() -> SpeedMedia:
#        return SpeedMedia(AudioSpeedService(), VideoSpeedService())

#    @staticmethod
#    def build_media_audio_extractor() -> MediaAudioExtractor:
#        return MediaAudioExtractor()