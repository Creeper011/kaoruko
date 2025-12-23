from discord.ext import commands

class TestCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command(name="mm")
    async def TestCommand(self, ctx: commands.Context) -> None:
        await ctx.send("hello, i'm working!")
