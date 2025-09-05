import discord
from discord.ext import commands
from discord import app_commands
import json, os

CONFIG_FILE = "suggestions.json"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        suggestion_channels = json.load(f)
        suggestion_channels = {int(k): v for k, v in suggestion_channels.items()}
else:
    suggestion_channels = {}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(suggestion_channels, f, indent=4)

class SuggestionView(discord.ui.View):
    def __init__(self, embed: discord.Embed):
        super().__init__(timeout=None)
        self.embed = embed
        self.voters_yes = set()
        self.voters_no = set()

    async def update_embed(self, interaction: discord.Interaction):
        self.embed.set_field_at(0, name="Votes", value=f"✅ Oui : {len(self.voters_yes)}\n❌ Non : {len(self.voters_no)}", inline=False)
        await interaction.message.edit(embed=self.embed, view=self)

    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.voters_yes:
            await interaction.response.send_message("❌ Vous avez déjà voté Oui.", ephemeral=True)
            return
        if user_id in self.voters_no:
            self.voters_no.remove(user_id)
        self.voters_yes.add(user_id)
        await self.update_embed(interaction)
        await interaction.response.send_message("✅ Votre vote Oui a été pris en compte.", ephemeral=True)

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.voters_no:
            await interaction.response.send_message("❌ Vous avez déjà voté Non.", ephemeral=True)
            return
        if user_id in self.voters_yes:
            self.voters_yes.remove(user_id)
        self.voters_no.add(user_id)
        await self.update_embed(interaction)
        await interaction.response.send_message("✅ Votre vote Non a été pris en compte.", ephemeral=True)

class SuggestionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pannel_suggestion", description="Définir le salon où les suggestions apparaissent")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    async def panel_suggestion(self, interaction: discord.Interaction, salon: discord.TextChannel):
        suggestion_channels[interaction.guild.id] = salon.id
        save_config()
        await interaction.response.send_message(f"✅ Les suggestions iront dans {salon.mention}", ephemeral=True)

    @app_commands.command(name="suggestion", description="Envoyer une suggestion")
    async def suggestion(self, interaction: discord.Interaction, titre: str, description: str):
        guild_id = interaction.guild.id
        if guild_id not in suggestion_channels:
            await interaction.response.send_message("⚠️ Aucun salon de suggestions défini.", ephemeral=True)
            return

        salon = interaction.guild.get_channel(suggestion_channels[guild_id])
        if salon is None:
            await interaction.response.send_message("⚠️ Le salon défini n'existe plus.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"SUGGESTION : {titre}",
            description=f"MESSAGE : {description} ",
            color=discord.Color.from_rgb(18, 18, 18)  # Fond très sombre
        )
        embed.set_footer(text=f"By {interaction.user.display_name}")
        embed.add_field(name="Votes", value="✅ Oui : 0\n❌ Non : 0", inline=False)

        view = SuggestionView(embed)
        await salon.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Suggestion envoyée !", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SuggestionsCog(bot))
