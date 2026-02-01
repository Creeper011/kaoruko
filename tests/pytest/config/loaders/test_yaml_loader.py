from unittest.mock import MagicMock, mock_open, patch
from src.core.constants import DEFAULT_ENV_CONFIG_PATH
from src.infrastructure.services.config.loaders.yaml_loader import YamlLoader

def test_yaml_loader_load_success() -> None:
    mock_yaml_content = "key1: value1\nkey2: 2"
    logger_mock = MagicMock()
    yaml_loader = YamlLoader(logger=logger_mock, config_path=DEFAULT_ENV_CONFIG_PATH)

    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        data = yaml_loader.load()

    assert data == {"key1": "value1", "key2": 2}
    logger_mock.debug.assert_called_with(
        f"Successfully loaded yaml file on: {DEFAULT_ENV_CONFIG_PATH}"
    )

def test_yaml_loader_with_invalid_path() -> None:
    """Tests loading yaml loader with a invalid path"""
    logger_mock = MagicMock()
    invalid_path = DEFAULT_ENV_CONFIG_PATH.parent / "a_super_duper_random_yaml_non_existent_file.yaml"
    yaml_loader = YamlLoader(logger=logger_mock, config_path=invalid_path)

    try:
        yaml_loader.load()
    except Exception as error:
        assert str(error) == f"Yaml file not found: {invalid_path}"
        logger_mock.error.assert_called_with(f"Yaml file not found: {invalid_path}")

def test_yaml_loader_with_malformed_yaml() -> None:
    logger_mock = MagicMock()
    malformed_yaml_content = "key1: value1\nkey2 value2"  # Missing colon

    with patch("builtins.open", mock_open(read_data=malformed_yaml_content)):
        try:
            yaml_loader = YamlLoader(logger=logger_mock, config_path=DEFAULT_ENV_CONFIG_PATH)
            yaml_loader.load()
        except Exception as error:
            assert str(error).startswith("Error on loading yaml file: while scanning a simple key")

def test_yaml_loader_with_empty_yaml() -> None:
    logger_mock = MagicMock()
    empty_yaml_content = ""

    with patch("builtins.open", mock_open(read_data=empty_yaml_content)):
        yaml_loader = YamlLoader(logger=logger_mock, config_path=DEFAULT_ENV_CONFIG_PATH)
        data = yaml_loader.load()
    assert data == {}


def test_yaml_loader_logger() -> None:
    logger_mock = MagicMock()
    yaml_loader = YamlLoader(logger=logger_mock, config_path=DEFAULT_ENV_CONFIG_PATH)

    assert yaml_loader.logger == logger_mock

def test_yaml_loader_with_a_non_utf8_file() -> None:
    malformed_yaml_content = b"\x80\x81\x82"  # Invalid UTF-8 bytes
    logger_mock = MagicMock()

    with patch("builtins.open", mock_open(read_data=malformed_yaml_content)):
        try:
            yaml_loader = YamlLoader(logger=logger_mock, config_path=DEFAULT_ENV_CONFIG_PATH)
            yaml_loader.load()
        except Exception as error:
            assert str(error).startswith("Error on loading yaml file: unacceptable character")