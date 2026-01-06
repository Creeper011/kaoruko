from unittest.mock import MagicMock, patch
from pathlib import Path
from src.core.constants import DEFAULT_ENV_CONFIG_PATH
from src.infrastructure.services.config.loaders.env_loader import EnvLoader

def test_env_loader_load_success() -> None:
    logger_mock = MagicMock()
    
    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = True
    fake_path.resolve.return_value = "/fake/.env"
    fake_path.name = ".env"

    with patch("src.infrastructure.services.config.loaders.env_loader.load_dotenv"), \
         patch("src.infrastructure.services.config.loaders.env_loader.dotenv_values", 
               return_value={"key1": "value1", "key2": "value2"}):

        env_loader = EnvLoader(logger=logger_mock, config_path=fake_path)
        data = env_loader.load()

    assert data == {"key1": "value1", "key2": "value2"}
    fake_path.exists.assert_called_once()

def test_env_loader_with_invalid_path() -> None:
    logger_mock = MagicMock()
    
    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = False
    fake_path.resolve.return_value = "/path/invalido/.env"

    env_loader = EnvLoader(logger=logger_mock, config_path=fake_path)
    
    try:
        env_loader.load()
    except Exception as error:
        assert str(error) == f".env file not found at path: {fake_path.resolve()}"
        logger_mock.warning.assert_called()

def test_env_loader_with_generic_error() -> None:
    logger_mock = MagicMock()
    
    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = True
    fake_path.resolve.return_value = "/fake/.env"

    error_msg = "Simulated parsing error"
    with patch("src.infrastructure.services.config.loaders.env_loader.load_dotenv"), \
         patch("src.infrastructure.services.config.loaders.env_loader.dotenv_values", 
               side_effect=Exception(error_msg)):

        try:
            env_loader = EnvLoader(logger=logger_mock, config_path=fake_path)
            env_loader.load()
        except Exception as error:
            assert str(error) == f"Error loading .env file: {error_msg}"
            logger_mock.exception.assert_called()

def test_env_loader_with_empty_env() -> None:
    logger_mock = MagicMock()
    
    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = True

    with patch("src.infrastructure.services.config.loaders.env_loader.load_dotenv"), \
         patch("src.infrastructure.services.config.loaders.env_loader.dotenv_values", return_value={}):

        env_loader = EnvLoader(logger=logger_mock, config_path=fake_path)
        data = env_loader.load()
        
    assert data == {}

def test_env_loader_logger() -> None:
    logger_mock = MagicMock()
    env_loader = EnvLoader(logger=logger_mock, config_path=DEFAULT_ENV_CONFIG_PATH)
    assert env_loader.logger == logger_mock