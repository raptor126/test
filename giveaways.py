import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import datetime

# ======================
# VIEW POUR LE GIVEAWAY
# ======================
class GiveawayView(discord.ui.View):
    def __init__(self, duree: int, prix: str, author_id: int):
        super().__init__(timeout=duree)
        self.prix = prix
        self.participants = set()
        self.author_id = author_id
        self.winner = None
        self._view_message = None

    @discord.ui.button(label="🎉 Participer", style=discord.ButtonStyle.blurple)
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("❌ Vous participez déjà !", ephemeral=True)
            return
        self.participants.add(interaction.user.id)
        await interaction.response.send_message("✅ Vous participez au giveaway !", ephemeral=True)

    async def on_timeout(self):
        if not self._view_message:
            return

        embed = self._view_message.embeds[0]

        if self.participants:
            winner_id = random.choice(list(self.participants))
            self.winner = winner_id
            winner = self._view_message.guild.get_member(winner_id)

            embed.clear_fields()
            color=discord.Color.from_rgb(18, 18, 18)
            embed.add_field(name="🏆 Gagnant", value=winner.mention, inline=False)
            embed.add_field(name="🎁 Prix", value=self.prix, inline=False)
            embed.set_footer(text="Giveaway terminé")

            await self._view_message.edit(embed=embed, view=None)
            await self._view_message.channel.send(
                f"🎉 Félicitations {winner.mention} ! Tu as gagné **{self.prix}** 🎁"
            )
        else:
            embed.clear_fields()
            color=discord.Color.from_rgb(18, 18, 18)
            embed.add_field(name="🚫 Résultat", value="Aucun participant", inline=False)
            embed.add_field(name="🎁 Prix", value=self.prix, inline=False)
            embed.set_footer(text="Giveaway terminé")

            await self._view_message.edit(embed=embed, view=None)
            await self._view_message.channel.send("❌ Giveaway terminé, pas de participants.")

# ======================
# COG GIVEAWAYS
# ======================
class GiveawaysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /start_giveaway
    @app_commands.command(name="start_giveaway", description="Lancer un giveaway")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def start_giveaway(
        self, interaction: discord.Interaction,
        jours: int, heures: int, minutes: int, prix: str
    ):
        duree = (jours * 86400) + (heures * 3600) + (minutes * 60)
        if duree <= 0:
            await interaction.response.send_message("❌ La durée doit être supérieure à 0.", ephemeral=True)
            return

        end_time = int(datetime.datetime.utcnow().timestamp() + duree)

        embed = discord.Embed(
            title="🎉 Giveaway 🎉",
            description=f"🎁 **Prix : {prix}**\n\nCliquez sur le bouton 🎉 pour participer !",
            color=discord.Color.blurple()
        )
        embed.add_field(name="⏳ Se termine", value=f"<t:{end_time}:R>", inline=False)
        embed.set_footer(text=f"Lancé par {interaction.user.display_name}")

        view = GiveawayView(duree=duree, prix=prix, author_id=interaction.user.id)
        msg = await interaction.channel.send(embed=embed, view=view)
        view._view_message = msg

        # ✅ Répondre immédiatement à l'interaction pour éviter le freeze
        await interaction.response.send_message("✅ Giveaway lancé !", ephemeral=True)

        # ⚡ Lancer la gestion du timeout en arrière-plan
        asyncio.create_task(view.wait())

    # /reroll_giveaway
    @app_commands.command(name="reroll_giveaway", description="Relancer un gagnant pour un giveaway")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def reroll_giveaway(self, interaction: discord.Interaction, message_id: str):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except:
            await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)
            return

        if not msg.embeds:
            await interaction.response.send_message("❌ Ce message n'est pas un giveaway valide.", ephemeral=True)
            return

        await interaction.response.send_message(
            "⚠️ Le reroll automatique nécessite de sauvegarder les participants en base de données. "
            "Actuellement, ce n'est pas possible.", ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawaysCog(bot))
