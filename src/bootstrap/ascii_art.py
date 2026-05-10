"""This module provides a class for printing ASCII art."""
from logging import Logger

class AsciiArt():
    """This class is responsible for printing the ASCII art."""

    @staticmethod
    def print_ascii_art(logger: Logger) -> None:
        """
        Prints the ASCII art to the provided logger.

        Args:
            logger: The logger instance to use for printing the art.
        """
        art = r"""
 __  __     ______     ______     ______     __  __     __  __     ______
/\ \/ /    /\  __ \   /\  __ \   /\  == \   /\ \/\ \   /\ \/ /    /\  __ \
\ \  _"-.  \ \  __ \  \ \ \/\ \  \ \  __<   \ \ \_\ \  \ \  _"-.  \ \ \/\ \
 \ \_\ \_\  \ \_\ \_\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_\ \_\  \ \_____\
  \/_/\/_/   \/_/\/_/   \/_____/   \/_/ /_/   \/_____/   \/_/\/_/   \/_____/


"""
        roof_message = "Kaoruko initialized!"

        color_code = "\033[38;2;207;68;58m"
        reset_code = "\033[0m"

        logger.info(f"{color_code}{art}{reset_code}{roof_message}")