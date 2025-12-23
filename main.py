import asyncio
import logging

from src.bootstrap.application_builder import ApplicationBuilder


async def main() -> None:
    """The main entry point for the application."""
    # Logging is now configured inside ApplicationBuilder
    logger = logging.getLogger(__name__)
    logger.info("Starting application build...")

    try:
        builder = ApplicationBuilder()

        application = await builder.build()

        await application.run()

    except Exception as error:
        logger.critical(
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