from typing import Optional, Protocol, runtime_checkable
from src.domain.interfaces.dto.output.ship_output import ShipOutput

@runtime_checkable
class ShipProtocol(Protocol):
    def __init__(self, first_user_name: str, first_user_url: str, 
                first_user_id: int, second_user_name: str, second_user_id: int,
                second_user_url: str):
        ...
        
    async def __aenter__(self) -> "ShipProtocol":
        ...

    async def __aexit__(self, exc_type, exc_val, tb) -> None:
        ...

    async def get_response(self) -> ShipOutput:
        """Fetches the ship response and returns a ShipOutput object."""
        ...