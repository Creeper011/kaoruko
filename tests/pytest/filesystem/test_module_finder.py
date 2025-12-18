import logging
from pathlib import Path
from unittest.mock import MagicMock
from discord.ext.commands import Cog
from src.infrastructure.filesystem.module_finder import ModuleFinder

def test_module_finder_finds_cogs_successfully():
    """
    Tests that ModuleFinder correctly finds all classes inheriting from
    commands.Cog in a specific directory.
    """
    # Arrange
    logger = logging.getLogger(__name__)
    # Point to the test cogs directory
    find_path = Path("tests/pytest/discord/cogs_for_test")
    # We are looking for classes of type Cog
    class_to_find = Cog
    
    module_finder = ModuleFinder(
        logger=logger,
        find_path=find_path,
        class_to_find=class_to_find
    )
    
    # Act
    found_classes = module_finder.find_classes()
    
    # Assert
    assert len(found_classes) == 3
    
    # Check if the found classes are the ones we expect
    found_class_names = {cls.__name__ for cls in found_classes}
    expected_class_names = {"DummyCog", "AnotherCog", "CogWithDeps"}
    assert found_class_names == expected_class_names

def test_module_finder_handles_non_existent_path():
    """
    Tests that ModuleFinder handles a non-existent path gracefully,
    returning an empty list.
    """
    # Arrange
    logger = logging.getLogger(__name__)
    find_path = Path("non_existent_directory_for_testing")
    class_to_find = Cog
    
    module_finder = ModuleFinder(
        logger=logger,
        find_path=find_path,
        class_to_find=class_to_find
    )
    
    # Act
    found_classes = module_finder.find_classes()
    
    # Assert
    assert len(found_classes) == 0
