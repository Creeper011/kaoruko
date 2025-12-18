import logging
from unittest.mock import MagicMock, Mock
from discord import Intents
from src.infrastructure.services.config.models.application_settings import BotSettings
from src.infrastructure.services.discord.factories.bot_factory import BotFactory

def test_bot_factory_creates_bot_correctly():
    """
    Tests that the BotFactory correctly instantiates and configures a bot.
    """
    # Arrange
    mock_logger = MagicMock(spec=logging.Logger)
    
    # Mock for the BaseBot class itself, to inspect how it's called
    mock_base_bot_class = MagicMock()
    
    # The factory is initialized with the class
    factory = BotFactory(basebot=mock_base_bot_class, logger=mock_logger)
    
    # Test settings
    test_intents = Intents.default()
    test_settings = BotSettings(
        prefix="!",
        token="test_token",
        intents=test_intents
    )
    
    # The bot type to be created (can be a mock or a real class)
    # We use a simple Mock here as the type check is not strict
    mock_bot_type = Mock() 

    # Act
    bot_instance = factory.create_bot(bot=mock_bot_type, settings=test_settings)
    
    # Assert
    # 1. Check if the BaseBot class was called to create an instance
    mock_base_bot_class.assert_called_once()
    
    # 2. Check if it was called with the correct arguments from settings
    mock_base_bot_class.assert_called_once_with(
        command_prefix=test_settings.prefix,
        intents=test_settings.intents,
        logger=mock_logger
    )
    
    # 3. Check if the returned instance is what the mocked BaseBot class returned
    assert bot_instance == mock_base_bot_class.return_value
