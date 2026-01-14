import time
import logging
from dataclasses import replace
from src.application.dto.output.download_output import DownloadOutput
from src.application.dto.request.download_request import DownloadRequest
from src.application.protocols.download_usecase_protocol import DownloadUseCaseProtocol

class TimedDownloadUseCase():
    def __init__(self, usecase: DownloadUseCaseProtocol, logger: logging.Logger):
        self.usecase = usecase
        self.logger = logger

    async def execute(self, request: DownloadRequest) -> DownloadOutput:
        start_time = time.perf_counter()
        
        result = await self.usecase.execute(request)
        elapsed_time = time.perf_counter() - start_time

        self.logger.info(f"Download process for {request.url} finished in {elapsed_time:.4f}s")

        result_with_time = replace(result, elapsed=elapsed_time)

        return result_with_time