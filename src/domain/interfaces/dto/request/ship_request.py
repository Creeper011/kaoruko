from dataclasses import dataclass
from src.domain.interfaces.dto.user import User

@dataclass
class ShipRequest:
    first_user: User
    second_user: User