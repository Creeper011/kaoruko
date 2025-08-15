from abc import ABC, abstractmethod

class DrivePort(ABC):
    @abstractmethod
    async def uploadToDrive(self, file_path: str) -> str:
        ...
