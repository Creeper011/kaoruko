"""
Kaoruko v2
Main entry point for the application.
Handles application startup and shutdown.
"""

import asyncio
import logging

from src.bootstrap.application_builder import ApplicationBuilder

async def main() -> None:
    """The main entry point for the application."""
    application = None

    try:
        builder = ApplicationBuilder()
        application = await builder.build()
        await application.run()

    except Exception as error:
        logging.getLogger(__name__).critical(
            "A critical error occurred during application startup",
            exc_info=error,
        )
    finally:
        if application:
            await application.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Application shut down by user.")
