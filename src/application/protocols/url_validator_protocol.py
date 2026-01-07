from typing import Protocol

class URLValidatorProtocol(Protocol):
    """Protocol for URL validator service."""

    def is_valid(self, url: str) -> bool:
        """Check if the given URL is valid.
        
        Args:
            url (str): The URL to validate.
        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        ...