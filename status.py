import discord
from discord.ext import commands
from discord import app_commands

class StatusCog(commands.Cog):
    """Cog pour changer le statut du bot via slash command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="status",
        description="Changer le statut du bot"
    )
    @app_commands.describe(texte="Texte du statut")
    @app_commands.choices(
        status_type=[
            app_commands.Choice(name="Joue", value="joue"),
            app_commands.Choice(name="Regarde", value="regarde"),
            app_commands.Choice(name="Écoute", value="écoute"),
            app_commands.Choice(name="Stream", value="stream")
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)  # Commande invisible pour les non-admin
    async def status(
        self,
        interaction: discord.Interaction,
        status_type: app_commands.Choice[str],
        texte: str
    ):
        """Change le statut du bot selon le type choisi."""
        if status_type.value == "joue":
            activity = discord.Game(name=texte)
        elif status_type.value == "regarde":
            activity = discord.Activity(type=discord.ActivityType.watching, name=texte)
        elif status_type.value == "écoute":
            activity = discord.Activity(type=discord.ActivityType.listening, name=texte)
        elif status_type.value == "stream":
            activity = discord.Streaming(name=texte, url="https://twitch.tv/discord")
        else:
            await interaction.response.send_message("❌ Type de statut invalide.", ephemeral=True)
            return

        await self.bot.change_presence(activity=activity)
        await interaction.response.send_message(
            f"✅ Statut changé en : **{status_type.name} {texte}**",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(StatusCog(bot))
