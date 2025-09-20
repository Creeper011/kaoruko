
import mimetypes
from src.domain.interfaces.dto.output.extract_audio_output import ExtractAudioOutput
from src.domain.interfaces.dto.request.extract_audio_request import ExtractAudioRequest
from src.domain.interfaces.protocols.extract_audio_protocol import ExtractAudioProtocol
from src.domain.exceptions import InvalidExtractAudioRequest

class ExtractAudioUsecase:
    """
    Use case responsible for extracting audio from a video.
    """

    def __init__(self, service: ExtractAudioProtocol):
        self.service = service

    def _validate(self, request: ExtractAudioRequest) -> bool:
        """Validate input and modify URL if needed."""
        if not request.url or not request.url.strip():
            raise InvalidExtractAudioRequest("URL cannot be empty")
        

        if request.file_limit is not None and request.file_limit <= 0:
            raise InvalidExtractAudioRequest("File limit must be greater than zero")
        
        if request.file_limit is not None and request.file_size > request.file_limit:
            raise InvalidExtractAudioRequest(
                f"File size {request.file_size} exceeds the limit of {request.file_limit} bytes"
            )

        mime_type, _ = mimetypes.guess_type(request.url)
        if not mime_type or not mime_type.startswith("video/"):
            raise InvalidExtractAudioRequest(f"Invalid MIME type: {mime_type}")
        
        return True

    async def execute(self, request: ExtractAudioRequest) -> ExtractAudioOutput:
        """
        Executes the extraction process.

        Args:
            request (ExtractAudioRequest): Contains URL.

        Returns:
            ExtractAudioOutput: The result of the extraction, including file path and metadata.

        Raises:
            InvalidExtractAudioRequest: If the request is invalid (validation not yet implemented).
        """
        if not self._validate(request):
            raise InvalidExtractAudioRequest()

        async with self.service(request.url) as service:
            output = await service.get_response()

        return output
1