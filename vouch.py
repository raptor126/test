import discord
from discord import app_commands
from discord.ext import commands
import json

CONFIG_FILE = "proof_config.json"

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

class ProofModal(discord.ui.Modal, title="Envoyer une vouch"):
    def __init__(self):
        super().__init__()
        # Input texte pour le message
        self.message_input = discord.ui.TextInput(
            label="Ton message",
            style=discord.TextStyle.paragraph,
            placeholder="Écris ici ton message"
        )
        self.add_item(self.message_input)

        # Input nombre d'étoiles
        self.stars_input = discord.ui.TextInput(
            label="Nombre d'étoiles (1 à 5)",
            style=discord.TextStyle.short,
            placeholder="Ex : 5"
        )
        self.add_item(self.stars_input)

        # Input texte pour le vendeur
        self.seller_input = discord.ui.TextInput(
            label="Quel vendeur",
            style=discord.TextStyle.short,
            placeholder="Nom du vendeur"
        )
        self.add_item(self.seller_input)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in config:
            await interaction.response.send_message("❌ Aucun salon de proof configuré !", ephemeral=True)
            return

        channel_id = config[guild_id]["proof_channel"]
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("❌ Le salon configuré n'existe pas !", ephemeral=True)
            return

        # Récupération des étoiles
        try:
            stars = int(self.stars_input.value)
            stars = max(1, min(5, stars))
        except:
            stars = 0

        # Création de l'embed
        embed = discord.Embed(
            title=f"Nouvelle vouch pour {self.seller_input.value}",
            description=self.message_input.value,
            color=discord.Color.from_rgb(18, 18, 18)  # Fond noir moderne
        )
        embed.add_field(name="Étoiles", value="⭐" * stars, inline=True)
        embed.add_field(name="Interactions", value="✅ : 0\n❤️ : 0", inline=False)
        embed.set_footer(text=f"Vouch envoyée par {interaction.user.display_name}")

        # Création de la vue avec boutons
        view = ProofView(embed)
        msg = await channel.send(embed=embed, view=view)
        view._message = msg  # Permet de mettre à jour l'embed sur le message

        await interaction.response.send_message("✅ Ta vouch a été envoyée !", ephemeral=True)

class ProofView(discord.ui.View):
    def __init__(self, embed: discord.Embed):
        super().__init__(timeout=None)
        self.embed = embed
        self.check_count = 0
        self.heart_count = 0
        self._message = None  # sera défini après l'envoi

    async def update_embed(self):
        self.embed.set_field_at(
            1, 
            name="Interactions", 
            value=f"✅ : {self.check_count}\n❤️ : {self.heart_count}", 
            inline=False
        )
        await self._message.edit(embed=self.embed, view=self)

    @discord.ui.button(label="✅ Valider", style=discord.ButtonStyle.green)
    async def check_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.check_count += 1
        await self.update_embed()
        await interaction.response.send_message(f"{interaction.user.mention} a validé cette vouch ✅", ephemeral=True)

    @discord.ui.button(label="❤️ J’aime", style=discord.ButtonStyle.red)
    async def heart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.heart_count += 1
        await self.update_embed()
        await interaction.response.send_message(f"{interaction.user.mention} a aimé cette vouch ❤️", ephemeral=True)

class Proof(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vouch", description="Envoyer un vouch avec message et étoiles")
    async def proof(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProofModal())

    @app_commands.command(name="pannel_vouch", description="Configurer le salon où les vouch seront envoyées")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    @app_commands.describe(channel="Le salon pour les vouch")
    async def pannel_proof(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        config[guild_id] = {"proof_channel": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ Salon de proof configuré : {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Proof(bot))