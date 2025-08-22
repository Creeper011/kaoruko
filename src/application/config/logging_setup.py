import logging

class LoggingSetup(logging.Logger):
    def __init__(self, is_debug: bool = False):
        level = logging.DEBUG if is_debug else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(module)s Line: %(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        super().__init__(__name__, level)