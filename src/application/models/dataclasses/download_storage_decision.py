from dataclasses import dataclass
from src.domain.enum.download_destination import DownloadDestination

@dataclass
class DownloadStorageDecision():
    destination: DownloadDestination
