from discord.ext import commands

class DummyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

class AnotherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

class NotACog:
    pass
