import discord
import logging
from discord.ext import commands
from src.infrastructure import ErrorTypes
from src.domain.usecases import ConvertToAudio
from src.domain.usecases import SpeedControlMedia
from src.infrastructure.bot.utils import create_error

logger = logging.getLogger(__name__)

class ToAudioCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_prefix = self.bot.command_prefix[1:]+"?"
        self.converter = ConvertToAudio()
        self.speed_audio = SpeedControlMedia()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.strip()
        if not content.lower().startswith(f"{self.bot_prefix.lower()}toaudio"):
            return 
        if not message.reference:
            return 
        try:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
        except Exception:
            return

        if not replied_message.attachments:
            await message.channel.send(embed=create_error(error="", type=ErrorTypes.INVALID_INPUT))
            return

        attachment = replied_message.attachments[0]
        if attachment.content_type is None or not attachment.content_type.startswith("video/"):
            await message.channel.send(embed=create_error(error="The replied message attachment is not a supported video.",
            type=ErrorTypes.INVALID_FILE_TYPE))
            return

        args = content.split()
        speed = 1.0
        preserve_pitch = False
        
        if len(args) > 1:
            try:
                speed = float(args[1].replace(",", "."))
                if speed <= 0.1 or speed > 2:
                    await message.channel.send(embed=create_error("Speed must be between 0.1 - 2.0",
                    type=ErrorTypes.INVALID_INPUT))
                    return
            except Exception:
                await message.channel.send(embed=create_error(error="Invalid speed input", 
                note=f"Example use: {self.bot_prefix}toaudio 1.5 [preserve_pitch]",
                type=ErrorTypes.INVALID_INPUT))
                return
        
        # Check for preserve_pitch option
        if len(args) > 2:
            if args[2].lower() in ['true', '1', 'yes', 'on', 'y']:
                preserve_pitch = True
            elif args[2].lower() in ['false', '0', 'no', 'off', 'n']:
                preserve_pitch = False
            else:
                await message.channel.send(embed=create_error(error="Invalid preserve_pitch option", 
                note=f"Example use: {self.bot_prefix}toaudio 1.5 true",
                type=ErrorTypes.INVALID_INPUT))
                return

        await message.channel.send("Processing...")

        # process logic
        process_path = None
        try:
            result, audio_path, process_path, convert_elapsed = await self.converter.toAudioFromAttachment(attachment)
            if not result.ok or audio_path is None:
                await message.channel.send(embed=create_error(error=f"Error converting video to audio.",
                code=f"{result.error}", type=result.type))
                return

            file_size = None
            if audio_path and audio_path.exists():
                file_size = audio_path.stat().st_size

            if speed != 1.0:
                speed_result = await self.speed_audio.change_speed(speed, preserve_pitch, audio_path)
                if not speed_result.filepath and not speed_result.drive_link:
                    await message.channel.send(embed=create_error(error=f"Error changing speed",
                    code=f"{speed_result}", type=ErrorTypes.UNKNOWN))
                    return
                
                # Use drive_link if available, otherwise use filepath
                if speed_result.drive_link:
                    pitch_info = f" (pitch preserved)" if preserve_pitch else ""
                    await message.channel.send(
                        content=f"Audio extracted with speed {speed}x{pitch_info}!\nFile size: {file_size / (1024 * 1024):.2f}MB, Convert time: {convert_elapsed:.2f}s, Speed time: {speed_result.elapsed:.2f}s\n(File too large, uploaded to Drive)\nUrl:{speed_result.drive_link}",
                    )
                    return
                else:
                    audio_path = speed_result.filepath

            speed_info = f" with speed {speed}x" if speed != 1.0 else ""
            pitch_info = f" (pitch preserved)" if speed != 1.0 and preserve_pitch else ""
            speed_time = speed_result.elapsed if speed != 1.0 else 0
            await message.channel.send(
                content=f"Audio extracted{speed_info}{pitch_info}!\nFile size: {file_size / (1024 * 1024):.2f}MB, Convert time: {convert_elapsed:.2f}s, Speed time: {speed_time:.2f}s",
                file=discord.File(audio_path, filename=audio_path.name)
            )
            
            # Cleanup after successful send
            if audio_path and audio_path.exists():
                try:
                    audio_path.unlink()
                except Exception:
                    pass
                    
        except Exception as error:
            await message.channel.send(embed=create_error(error="Unexpected error!", code=str(error),
            type=ErrorTypes.UNKNOWN))
        finally:
            # Ensure cleanup happens even if there's an error
            if process_path:
                self.converter._cleanup_process_path(process_path)

async def setup(bot: commands.Bot):
    await bot.add_cog(ToAudioCog(bot))