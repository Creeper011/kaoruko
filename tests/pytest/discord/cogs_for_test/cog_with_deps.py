from discord.ext import commands

# A dummy service class for type hinting
class DummyService:
    def some_method(self):
        return "data"

class CogWithDeps(commands.Cog):
    def __init__(self, bot: commands.Bot, service: DummyService):
        self.bot = bot
        self.service = service
