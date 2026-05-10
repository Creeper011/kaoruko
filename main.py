"""
Kaoruko v2
Main entry point for the application.
Handles application startup and shutdown.
"""

import asyncio
import logging

from src.bootstrap.application import Application

async def main() -> None:
    """The main entry point for the application."""
    application = None

    try:
        application = Application()
        await application.run()

    except Exception as error:
        logging.getLogger(__name__).critical(
            "A critical error occurred during application startup: %s",
            error,
        )
    finally:
        if application:
            await application.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Application shut down by user.")
