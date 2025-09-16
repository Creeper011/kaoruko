import hashlib
import random

class ShipCalculator:
    """Utility class to calculate a ship percentage and generate a ship name."""

    @staticmethod
    def calculate_percentage(first_user_id: int, second_user_id: int) -> int:
        """
        Return a ship compatibility percentage between two users (0-100).

        Args:
            first_user_id (int): ID of the first user.
            second_user_id (int): ID of the second user.

        Returns:
            int: Compatibility percentage between 0 and 100.
        """
        ship_id = f"{min(int(first_user_id), int(second_user_id))}:{max(int(first_user_id), int(second_user_id))}"
        hash_val = hashlib.sha256(ship_id.encode()).hexdigest()
        percent = int(hash_val[:2], 16) % 101
        percent += random.randint(1, 5)
        return min(percent, 100)

    @staticmethod
    def calculate_ship_name(first_user_name: str, second_user_name: str) -> str:
        """
        Return a ship name by combining halves of two usernames.

        Args:
            first_user_name (str): Name of the first user.
            second_user_name (str): Name of the second user.

        Returns:
            str: Combined ship name.
        """
        first_half = first_user_name[:len(first_user_name) // 2]
        second_half = second_user_name[len(second_user_name) // 2:]
        return first_half + second_half
