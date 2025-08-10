from discord.ext import commands
from src.domain.usecases.dynamiccogs import DynamicCogsUsecase
from src.infrastructure.constants import Result
from src.infrastructure.bot.utils import create_error

class DynamicCogsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.usecase_dynamicCog = DynamicCogsUsecase(self.bot)
    
    @commands.command(name="load")
    async def loadExtensionCommand(self, ctx: commands.Context, extension_name: str):
        result: Result = await self.usecase_dynamicCog.load_extension(extension_name)
        if result.ok:
            await ctx.send("Extension loaded!")
        else:
            await ctx.send(embed=create_error(error="Error on loading extension",
                                                        code=f"{result.error}", type=result.type))
    
    @commands.command(name="unload")
    async def unloadExtensionCommand(self, ctx: commands.Context, extension_name: str):
        result: Result = await self.usecase_dynamicCog.unload_extension(extension_name)
        if result.ok:
            await ctx.send("Extension unloaded!")
        else:
            await ctx.send(embed=create_error(error="Error on unloading extension",
                                                        code=f"{result.error}", type=result.type))
    
    @commands.command(name="reload")
    async def reloadExtensionCommand(self, ctx: commands.Context, extension_name: str):
        result: Result = await self.usecase_dynamicCog.reload_extension(extension_name)
        if result.ok:
            await ctx.send("Extension reloaded!")
        else:
            await ctx.send(embed=create_error(error="Error on reloading extension",
                                                        code=f"{result.error}", type=result.type))

async def setup(bot: commands.Bot):
    await bot.add_cog(DynamicCogsCog(bot))