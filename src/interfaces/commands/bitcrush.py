import asyncio
import discord
import logging
from discord.ext import commands
from discord import app_commands
from src.domain.usecases.bit_crusher import BitCrusherUsecase, BitCrushResult
from src.application.utils.error_embed import create_error
from src.application.constants import ErrorTypes

logger = logging.getLogger(__name__)

class BitcrushCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bitcrush", description="Apply bitcrush effect to audio")
    @app_commands.describe(attachment="The audio attachment to bitcrush",
                           audio_bit_depth="Bit depth for audio (1-32)",
                           audio_downsample="Downsample rate for audio",)
    @app_commands.choices(audio_downsample=[
            app_commands.Choice(name="8000 Hz", value=8000),
            app_commands.Choice(name="11025 Hz", value=11025),
            app_commands.Choice(name="12000 Hz", value=12000),
            app_commands.Choice(name="16000 Hz", value=16000),
            app_commands.Choice(name="22050 Hz", value=22050),
            app_commands.Choice(name="24000 Hz", value=24000),
            app_commands.Choice(name="32000 Hz", value=32000),
            app_commands.Choice(name="44100 Hz", value=44100),
            app_commands.Choice(name="48000 Hz", value=48000)
])
    async def bitcrush(self, interaction: discord.Interaction, attachment: discord.Attachment, audio_bit_depth: app_commands.Range[int, 1, 32] = 4, audio_downsample: app_commands.Choice[int] = 8000):
        await interaction.response.defer(thinking=True)

        if isinstance(audio_downsample, app_commands.Choice):
            audio_downsample = audio_downsample.value

        usecase = BitCrusherUsecase(audio_bit_depth, audio_downsample)
        result: BitCrushResult = await usecase.crush_media_attachement(attachment)

        try:
            if result.file_path and not result.drive_link:
                await interaction.followup.send("Sending crushed file...")
                file = discord.File(result.file_path)
                await interaction.edit_original_response(content=f"Crushed! Elapsed: {result.elapsed:.2f} seconds", attachments=[file])
            else:
                await interaction.edit_original_response(content=f"File too large, uploaded to drive: {result.drive_link}.\nElapsed: {result.elapsed:.2f} seconds")

        except Exception as error:
            logger.error(f"Error processing attachment {attachment.filename}: {error}")
            await interaction.edit_original_response(embed=create_error(error=str(error), type=ErrorTypes.UNKNOWN, code=str(error)))
            await asyncio.sleep(5)
            usecase._cleanup()
            return

        finally:
            await asyncio.sleep(5)
            usecase._cleanup()

async def setup(bot: commands.Bot):
    await bot.add_cog(BitcrushCommand(bot))