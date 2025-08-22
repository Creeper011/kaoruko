import argparse
from src.application.injector import Injector
from src.application.bot import Bot

CONFIG_PATH_YAML = "./config.yml"
ENV_PATH = ".env"

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", help="debug")
args = parser.parse_args()

if __name__ == "__main__":
    dependencies = Injector.inject(CONFIG_PATH_YAML, ENV_PATH, args.debug)
    bot = Bot(**dependencies)
    bot.run()