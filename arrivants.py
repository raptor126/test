import discord
from discord import app_commands
from discord.ext import commands
import json

CONFIG_FILE = "config.json"

@app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()

class Arrivants(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # S'assurer qu'on n'attache le listener qu'une seule fois
        if not hasattr(bot, "_welcome_listener_attached"):
            bot.add_listener(self.on_member_join)
            bot._welcome_listener_attached = True

    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id not in config:
            return

        channel_id = config[guild_id]["welcome_channel"]
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        # Vérifie si un message de bienvenue a déjà été envoyé pour ce membre
        async for msg in channel.history(limit=50):
            if f"{member.mention}" in msg.content:
                return  # Message déjà envoyé, on skip

        embed = discord.Embed(
            title="🎉 Bienvenue sur Nexode Store !",
            description=f"Salut {member.mention}, nous sommes ravis de t'accueillir !",
            color=discord.Color.from_rgb(18, 18, 18)  # Fond quasi noir
        )
        embed.set_thumbnail(url=member.avatar.url)  # Avatar du membre à droite

        await channel.send(embed=embed)

    @app_commands.command(name="pannel_arrivant", description="Configurer le salon d'accueil des nouveaux arrivants")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    @app_commands.describe(channel="Le salon où les messages de bienvenue seront envoyés")
    async def pannel_arrivant(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        config[guild_id] = {"welcome_channel": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ Salon d'accueil configuré : {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Arrivants(bot))