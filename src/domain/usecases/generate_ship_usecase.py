from src.domain.interfaces.protocols.ship_protocol import ShipProtocol
from src.domain.interfaces.dto.request.ship_request import ShipRequest
from src.domain.interfaces.dto.output.ship_output import ShipOutput
from src.domain.exceptions.ship_exceptions import InvalidShipRequest

class ShipUsecase:
    """
    Usecase responsible for processing a "ship" request between two users.

    It validates the input request and interacts with the service layer
    to generate a ShipOutput.
    """

    def __init__(self, service: ShipProtocol):
        """
        Initialize the usecase with a ship service.

        Args:
            service (ShipProtocol): The service responsible for handling the ship logic.
        """
        self.service = service

    def _validate(self, request: ShipRequest) -> bool:
        """
        Validate the given ShipRequest.

        Ensures that both users have a name and a profile image URL.

        Args:
            request (ShipRequest): The ship request to validate.

        Returns:
            bool: True if the request is valid, False otherwise.
        """
        if not request.first_user.name or not request.second_user.name:
            return False
        if not request.first_user.profile_image_url or not request.second_user.profile_image_url:
            return False
        return True

    async def execute(self, request: ShipRequest) -> ShipOutput:
        """
        Execute the ship usecase.

        Validates the request and then uses the provided service to
        generate the ShipOutput asynchronously.

        Args:
            request (ShipRequest): The ship request containing two users.

        Raises:
            InvalidShipRequest: If the request validation fails.

        Returns:
            ShipOutput: The output of the ship operation.
        """
        if not self._validate(request):
            raise InvalidShipRequest()
        
        async with self.service(
        request.first_user.name,
        request.first_user.profile_image_url,
        request.first_user.user_id,
        request.second_user.name,
        request.second_user.user_id, 
        request.second_user.profile_image_url
    ) as service:
            output = await service.get_response()

        return output