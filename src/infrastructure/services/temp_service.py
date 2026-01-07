import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from logging import Logger
import uuid
from typing import Optional
from src.core.constants import DEFAULT_TEMP_DIR

class TempService():
    """Service for managing temporary files and folders."""

    def __init__(self, logger: Logger, base_dir: Optional[Path] = DEFAULT_TEMP_DIR) -> None:
        self.logger = logger
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"TempService initialized at {self.base_dir}")

    @asynccontextmanager
    async def create_session(self) -> AsyncGenerator[Path, None]:
        temp_path = None

        try:
            session_id = uuid.uuid4().hex
            temp_path = self.base_dir / f"kaoruko_{session_id}"
            temp_path.mkdir()

            self.logger.debug(f"Created temp directory: {temp_path}")

            yield temp_path

        except Exception as error:
            self.logger.error(
                f"Error during temporary session: {error}",
                exc_info=True
            )
            raise

        finally:
            if temp_path and temp_path.exists():
                try:
                    shutil.rmtree(temp_path)
                    self.logger.debug(f"Cleaned up temp directory: {temp_path}")
                except Exception as error:
                    self.logger.warning(
                        f"Failed to cleanup temp directory {temp_path}: {error}"
                    )
