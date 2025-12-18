import pytest
import logging
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from discord.ext.commands import Bot, Cog
from src.infrastructure.filesystem.module_finder import ModuleFinder
from src.infrastructure.services.discord.utils.extension_loader import ExtensionLoader

# Import test classes from the test cogs directory
from tests.pytest.discord.cogs_for_test.cog_with_deps import DummyService, CogWithDeps
from tests.pytest.discord.cogs_for_test.dummy_cog import DummyCog, AnotherCog

@pytest.mark.asyncio
async def test_extension_loader_loads_cogs_and_injects_dependencies():
    """
    Tests that ExtensionLoader correctly finds all cogs, loads them,
    and injects the required services.
    """
    # Arrange
    mock_logger = MagicMock(spec=logging.Logger)
    
    # Mock the bot, needs an async add_cog method
    mock_bot = MagicMock(spec=Bot)
    mock_bot.add_cog = AsyncMock()
    
    # Use the real ModuleFinder pointing to our test cogs
    find_path = Path("tests/pytest/discord/cogs_for_test")
    module_finder = ModuleFinder(logger=mock_logger, find_path=find_path, class_to_find=Cog)
    
    # Create a mock service to be injected
    mock_dummy_service = MagicMock(spec=DummyService)
    
    # The services dictionary that the loader will use for injection
    services = {
        DummyService: mock_dummy_service
    }
    
    # Instantiate the loader
    extension_loader = ExtensionLoader(
        logger=mock_logger,
        bot=mock_bot,
        extension_finder=module_finder,
        services=services
    )
    
    # Act
    await extension_loader.load_extensions()
    
    # Assert
    # Three cogs should be found and loaded: DummyCog, AnotherCog, CogWithDeps
    assert mock_bot.add_cog.call_count == 3
    
    # Get the actual cog instances passed to add_cog
    # call_args_list[i][0][0] gets the first positional argument of the i-th call
    loaded_cogs = [call.args[0] for call in mock_bot.add_cog.call_args_list]
    
    # Check that instances of all our test cogs are in the list of loaded cogs
    assert any(isinstance(cog, DummyCog) for cog in loaded_cogs)
    assert any(isinstance(cog, AnotherCog) for cog in loaded_cogs)
    assert any(isinstance(cog, CogWithDeps) for cog in loaded_cogs)
    
    # Find the CogWithDeps instance and check if the service was injected
    cog_with_deps_instance = next((cog for cog in loaded_cogs if isinstance(cog, CogWithDeps)), None)
    assert cog_with_deps_instance is not None
    assert cog_with_deps_instance.service is mock_dummy_service
