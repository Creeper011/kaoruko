import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands
from src.application.constants.error_types import ErrorTypes
from src.application.utils.error_embed import create_error
from src.domain.interfaces.dto.request.extract_audio_request import ExtractAudioRequest
from src.domain.exceptions import InvalidExtractAudioRequest

logger = logging.getLogger(__name__)

class ExtractAudioCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _cleanup(self, audio_output):
        logger.debug("Starting cleanup process...")
        await asyncio.sleep(1)
        if audio_output:
            logger.debug("Audio Output exists! Cleaning up audio output...")
            if callable(audio_output.cleanup):
                if asyncio.iscoroutinefunction(audio_output.cleanup):
                    logger.debug("Cleanup is a coroutine function, awaiting it...")
                    await audio_output.cleanup()
                else:
                    logger.debug("Cleanup is a regular function, calling it...")
                    audio_output.cleanup()

    @app_commands.command(name="extract_audio", description="Extract audio from a attachment")
    @app_commands.describe(
        attachment="The attachment to extract audio from",
        invisible="If True, only you will see the result (ephemeral message)",
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def extract_audio(self, interaction: discord.Interaction, attachment: discord.Attachment, invisible: bool = False):
        """Extract audio from a video attachment."""
        await interaction.response.defer(ephemeral=invisible)

        audio_output = None
        try:
            usecase = self.bot.container.build_extract_audio_usecase()
            logger.debug("ExtractAudioUsecase built successfully")
            request = ExtractAudioRequest(url=attachment.url,
                                          file_size=attachment.size)
            if interaction.is_guild_integration():
                if interaction.guild.filesize_limit <= 25 * 1024 * 1024:
                    request.file_limit = 120 * 1024 * 1024 
                else:
                    request.file_limit = interaction.guild.filesize_limit
            else:
                request.file_limit = None

            logger.debug(f"ExtractAudioRequest created with URL: {request.url}")
            audio_output = await usecase.execute(request)

            logger.debug(f"Audio extraction completed, file path: {audio_output.file_path}, elapsed time: {audio_output.elapsed:.2f}s")
            await interaction.followup.send(content=f"Extraction Completed! Elapsed {audio_output.elapsed:.2f}s", 
                file=discord.File(audio_output.file_path), ephemeral=invisible)
            
        except Exception as error:
            error_embed = create_error(ErrorTypes.UNKNOWN, str(error))
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            await self._cleanup(audio_output)

        except InvalidExtractAudioRequest as error:
            logger.error(f"InvalidExtractAudioRequest: {error}")
            error_embed = create_error(ErrorTypes.INVALID_INPUT, str(error))
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            await self._cleanup(audio_output)

        finally:
            logger.debug("Entering final cleanup phase")
            await self._cleanup(audio_output)

    @commands.command(name="toaudio", aliases=["ta"])
    async def toaudio(self, ctx: commands.Context): 
        """Extract audio from a video attachment or a replied message with an attachment."""

        await ctx.send("Processing")
        audio_output = None

        try:
            async with ctx.typing():
                if ctx.message.reference:
                    referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                    if referenced_message.attachments:
                        attachment = referenced_message.attachments[0]
                    else:
                        await ctx.send("The replied message has no attachments.")
                        return
                elif not ctx.message.attachments:
                    await ctx.send("Please provide a video attachment or reply to a message with an attachment.")
                    return
                else:
                    attachment = ctx.message.attachments[0]

                usecase = self.bot.container.build_extract_audio_usecase()
                logger.debug("ExtractAudioUsecase built successfully")
                request = ExtractAudioRequest(url=attachment.url, file_size=attachment.size)
                if ctx.guild:
                    if ctx.guild.filesize_limit <= 25 * 1024 * 1024:
                        request.file_limit = 120 * 1024 * 1024 
                    else:
                        request.file_limit = ctx.guild.filesize_limit
                else:
                    request.file_limit = None

                logger.debug(f"ExtractAudioRequest created with URL: {request.url}")
                audio_output = await usecase.execute(request)

            if audio_output:
                logger.debug(f"Audio extraction completed, file path: {audio_output.file_path}, elapsed time: {audio_output.elapsed:.2f}s")
                await ctx.send(content=f"Extraction Completed! Elapsed {audio_output.elapsed:.2f}s", 
                            file=discord.File(audio_output.file_path))
            
        except InvalidExtractAudioRequest as error:
            logger.error(f"InvalidExtractAudioRequest: {error}")
            error_embed = create_error(ErrorTypes.INVALID_INPUT, str(error))
            await ctx.send(embed=error_embed)
        except Exception as error:
            error_embed = create_error(ErrorTypes.UNKNOWN, str(error))
            await ctx.send(embed=error_embed)
        finally:
            logger.debug("Entering final cleanup phase")
            await self._cleanup(audio_output)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(ExtractAudioCog(bot))