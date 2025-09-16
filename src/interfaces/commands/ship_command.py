import discord
from discord.ext import commands
from discord import app_commands
from src.application.builderman import BuilderMan
from src.application.utils.error_embed import create_error
from src.application.constants.error_types import ErrorTypes
from src.domain.interfaces.dto.request.ship_request import ShipRequest
from src.domain.interfaces.dto.output.ship_output import ShipOutput
from src.domain.interfaces.dto.user import User
import io

class ShipCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.builder = BuilderMan()

    @app_commands.command(name="ship", description="ship bro")
    async def ship_command(self, interaction: discord.Interaction, user1: discord.User, user2: discord.User):
        await interaction.response.defer(thinking=True)

        request = ShipRequest(
            User(
                name=user1.name,
                user_id=user1.id,
                profile_image_url=user1.avatar.url
            ),
            User(
                name=user2.name,
                user_id=user2.id,
                profile_image_url=user2.avatar.url
            ),
        )

        try: 
            service = self.builder.build_ship_usecase()
            response: ShipOutput = await service.execute(request)

            # Cria arquivo da imagem
            image_file = discord.File(io.BytesIO(response.image_bytes), filename="ship.png")

            # Cria embed
            embed = discord.Embed(
                title=f"💖 {response.ship_name} 💖",
                description=f"Compatibilidade: {response.provability}%",
                color=discord.Color.purple()
            )
            embed.set_image(url="attachment://ship.png")

            # Envia resposta
            await interaction.followup.send(embed=embed, file=image_file)

        except Exception as error:
            await interaction.followup.send(
                embed=create_error(
                    error="An unexpected error has occurred",
                    code=str(error),
                    type=ErrorTypes.UNKNOWN
                )
            )
            raise error

async def setup(bot: commands.Bot):
    await bot.add_cog(ShipCog(bot))