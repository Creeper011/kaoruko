from src.domain.interfaces.dto.output.ship_output import ShipOutput
from src.infrastructure.services.ship import ShipImageGenerator, ShipCalculator
import io

class ShipOrchestrator:
    """
    Orchestrates the "ship" process between two users by calculating 
    a ship name, a compatibility percentage, and generating a ship image.

    Attributes:
        first_user_name (str): Name of the first user.
        first_user_url (str): URL of the first user's image.
        first_user_id (int): Unique ID of the first user.
        second_user_name (str): Name of the second user.
        second_user_url (str): URL of the second user's image.
        second_user_id (int): Unique ID of the second user.
        ship_image_service (ShipImageGenerator | None): Service to generate ship images.
        ship_name (str | None): Calculated ship name.
        percentage (int | None): Calculated compatibility percentage.
        image_bytes (bytes | None): Generated ship image in bytes.
    """

    def __init__(self, first_user_name: str, first_user_url: str, 
                 first_user_id: int, second_user_name: str, second_user_id: int,
                 second_user_url: str):
        """
        Initializes the ShipOrchestrator with user data.

        Args:
            first_user_name (str): Name of the first user.
            first_user_url (str): URL of the first user's image.
            first_user_id (int): Unique ID of the first user.
            second_user_name (str): Name of the second user.
            second_user_id (int): Unique ID of the second user.
            second_user_url (str): URL of the second user's image.
        """
        self.first_user_name = first_user_name
        self.first_user_url = first_user_url
        self.first_user_id = first_user_id
        self.second_user_name = second_user_name
        self.second_user_id = second_user_id
        self.second_user_url = second_user_url

        self.ship_image_service: ShipImageGenerator | None = None
        self.ship_name: str | None = None
        self.percentage: int | None = None
        self.image_bytes: bytes | None = None

    async def __aenter__(self):
        """
        Async context manager entry. Computes ship data and prepares resources.

        Returns:
            ShipOrchestrator: Self with mounted data.
        """
        self._mount_data()
        return self

    async def __aexit__(self, exc_type, exc_val, tb) -> None:
        """
        Async context manager exit. Cleans up resources.

        Args:
            exc_type (type): Exception type, if any.
            exc_val (Exception): Exception instance, if any.
            tb (traceback): Traceback object, if any.
        """
        self.ship_image_service = None

    def _mount_data(self):
        """
        Calculates ship name, compatibility percentage, and generates the ship image bytes.

        This method is intended to be called internally during context manager entry.
        """
        self.ship_name = ShipCalculator.calculate_ship_name(
            first_user_name=self.first_user_name,
            second_user_name=self.second_user_name
        )

        self.percentage = ShipCalculator.calculate_percentage(
            first_user_id=self.first_user_id,
            second_user_id=self.second_user_id
        )

        self.ship_image_service = ShipImageGenerator(
            first_user_name=self.first_user_name,
            second_user_name=self.second_user_name,
            image_url_first_user=self.first_user_url,
            image_url_second_user=self.second_user_url,
            percentage=self.percentage
        )

        self.image_bytes = self.ship_image_service.get_image()

    async def get_response(self) -> ShipOutput:
        """
        Constructs and returns the ShipOutput DTO using precomputed data.

        Returns:
            ShipOutput: Data transfer object containing ship name, 
                        provability percentage, and image bytes.
        """
        return ShipOutput(
            provability=self.percentage,
            ship_name=self.ship_name,
            image_bytes=self.image_bytes
        )
