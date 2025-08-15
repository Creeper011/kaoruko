from src.domain.ports.drive_port import DrivePort
from src.infrastructure.services.drive import Drive

class DriveAdapter(DrivePort):
    def __init__(self):
        self._drive = Drive("")

    async def uploadToDrive(self, file_path: str) -> str:
        return await self._drive.uploadToDrive(file_path)
