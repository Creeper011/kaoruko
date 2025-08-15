import time
import platform
import distro
import discord
from discord import app_commands
from discord.ext import commands

class BotInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="info", description="Get info about the bot")
    async def info(self, interaction: discord.Interaction, invisible: bool = False):
        await interaction.response.defer(thinking=True, ephemeral=invisible)

        gw_ping = round(self.bot.latency * 1000)

        # rest ping (http)
        start = time.monotonic()
        await self.bot.http.request(discord.http.Route('GET', '/gateway'))
        rest_ping = round((time.monotonic() - start) * 1000)

        message = (
            f"Bot info 📦\n"
            f"> Name: {self.bot.user.name}\n"
            f"> Shards: {self.bot.shard_count}\n"
            f"> Shard ID: {self.bot.shard_id}\n"
            f"> Running on system: {distro.name()} ({platform.system()})\n"
            f"> Running on: Python {__import__('platform').python_version()}\n"
            f"> Gateway ping: {gw_ping} ms\n"
            f"> REST ping: {rest_ping} ms"
        )
        await interaction.followup.send(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(BotInfo(bot))