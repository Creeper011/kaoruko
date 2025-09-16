from dataclasses import dataclass

@dataclass
class ShipOutput():
    provability: float
    ship_name: str
    image_bytes: bytes
