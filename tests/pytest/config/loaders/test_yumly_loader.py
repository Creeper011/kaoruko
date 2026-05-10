from pathlib import Path
from unittest.mock import MagicMock, patch

from yumly import YumlyError

from src.constants import DEFAULT_YUMLY_CONFIG_PATH
from src.services.config.loaders.yumly_loader import YumlyLoader


def test_yumly_loader_load_success() -> None:
    logger_mock = MagicMock()

    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = True
    fake_path.resolve.return_value = "/fake/fig.yumly"
    fake_path.name = "fig.yumly"

    yumly_instance = MagicMock()
    yumly_instance.validate_file.return_value = True
    yumly_instance.load.return_value = {"application": {"version": "0.0.1"}}

    with patch("src.services.config.loaders.yumly_loader.Yumly", return_value=yumly_instance):
        yumly_loader = YumlyLoader(logger=logger_mock, config_path=fake_path)
        data = yumly_loader.load()

    assert data == {"application": {"version": "0.0.1"}}
    fake_path.exists.assert_called_once()
    yumly_instance.validate_file.assert_called_once()
    yumly_instance.load.assert_called_once()


def test_yumly_loader_with_invalid_path() -> None:
    logger_mock = MagicMock()

    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = False
    fake_path.resolve.return_value = "/path/invalido/fig.yumly"

    yumly_loader = YumlyLoader(logger=logger_mock, config_path=fake_path)

    try:
        yumly_loader.load()
    except Exception as error:
        assert str(error) == f"Yumly file not found at path: {fake_path.resolve()}"
        logger_mock.error.assert_called_with(f"Yumly file not found at path: {fake_path.resolve()}")


def test_yumly_loader_with_validation_failure() -> None:
    logger_mock = MagicMock()

    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = True
    fake_path.resolve.return_value = "/fake/fig.yumly"

    yumly_instance = MagicMock()
    yumly_instance.validate_file.return_value = False

    with patch("src.services.config.loaders.yumly_loader.Yumly", return_value=yumly_instance):
        yumly_loader = YumlyLoader(logger=logger_mock, config_path=fake_path)

        try:
            yumly_loader.load()
        except Exception as error:
            assert str(error) == f"Yumly validation failed for file: {fake_path.resolve()}"


def test_yumly_loader_with_non_mapping_result() -> None:
    logger_mock = MagicMock()

    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = True
    fake_path.resolve.return_value = "/fake/fig.yumly"

    yumly_instance = MagicMock()
    yumly_instance.validate_file.return_value = True
    yumly_instance.load.return_value = ["not", "a", "dict"]

    with patch("src.services.config.loaders.yumly_loader.Yumly", return_value=yumly_instance):
        yumly_loader = YumlyLoader(logger=logger_mock, config_path=fake_path)

        try:
            yumly_loader.load()
        except Exception as error:
            assert str(error) == f"Yumly file did not return a mapping: {fake_path.resolve()}"


def test_yumly_loader_with_yumly_error() -> None:
    logger_mock = MagicMock()

    fake_path = MagicMock(spec=Path)
    fake_path.exists.return_value = True
    fake_path.resolve.return_value = "/fake/fig.yumly"

    yumly_instance = MagicMock()
    yumly_instance.validate_file.side_effect = YumlyError("Simulated Yumly error")

    with patch("src.services.config.loaders.yumly_loader.Yumly", return_value=yumly_instance):
        try:
            yumly_loader = YumlyLoader(logger=logger_mock, config_path=fake_path)
            yumly_loader.load()
        except Exception as error:
            assert str(error) == "Error loading Yumly file: Simulated Yumly error"
            logger_mock.exception.assert_called()


def test_yumly_loader_logger() -> None:
    logger_mock = MagicMock()

    with patch("src.services.config.loaders.yumly_loader.Yumly"):
        yumly_loader = YumlyLoader(logger=logger_mock, config_path=DEFAULT_YUMLY_CONFIG_PATH)

    assert yumly_loader.logger == logger_mock
