import pkgutil
import importlib
import inspect
from pathlib import Path
from logging import Logger

class ModuleFinder():
    """Module finder class to find classes in a given path and return his module"""

    def __init__(self, logger: Logger, find_path: Path, class_to_find: type) -> None:
        self.logger = logger
        self.find_path = find_path
        if not isinstance(self.find_path, Path):
            raise TypeError("Find_path should be an Path object")
        self.class_to_find = class_to_find

    def find_classes(self) -> list[type]:
        """Find all classes in the given path and return his module"""
        classes = []
        module_path = str(self.find_path).replace('/', '.')

        for _, name, _ in pkgutil.iter_modules([str(self.find_path)]):
            try:
                module = importlib.import_module(f"{module_path}.{name}")
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if inspect.isclass(item) and issubclass(item, self.class_to_find) and item is not self.class_to_find:
                        classes.append(item)
            except Exception as e:
                self.logger.error(f"Could not import module '{name}' from '{self.find_path}': {e}")

        self.logger.debug(f"Found {len(classes)} classes in {self.find_path.absolute()}")
        return classes
