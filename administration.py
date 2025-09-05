import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # Enregistre les commandes slash dans le CommandTree
    @commands.Cog.listener()
    async def on_ready(self):
        try:
            synced = await self.bot.tree.sync()
            print(f"✅ {len(synced)} commandes slash synchronisées.")
        except Exception as e:
            print(f"Erreur de synchronisation : {e}")

    # ----------------------------
    # CLEAR
    # ----------------------------
    @app_commands.command(name="clear", description="Supprime un nombre de messages")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Le nombre doit être supérieur à 0.", ephemeral=True)
            return
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"✅ {amount} messages supprimés.", ephemeral=True)

    # ----------------------------
    # BAN
    # ----------------------------
    @app_commands.command(name="ban", description="Bannir un membre")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
        if member == interaction.user:
            await interaction.response.send_message("❌ Vous ne pouvez pas vous bannir vous-même.", ephemeral=True)
            return
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 {member.mention} a été banni. Raison : {reason}")

    # ----------------------------
    # KICK
    # ----------------------------
    @app_commands.command(name="kick", description="Expulser un membre")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admin    
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
        if member == interaction.user:
            await interaction.response.send_message("❌ Vous ne pouvez pas vous expulser vous-même.", ephemeral=True)
            return
        await member.kick(reason=reason)
        await interaction.response.send_message(f"👢 {member.mention} a été expulsé. Raison : {reason}")

    # ----------------------------
    # MUTE
    # ----------------------------
    @app_commands.command(name="mute", description="Mute un membre pendant X minutes")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Aucune raison fournie"):
        if minutes <= 0:
            await interaction.response.send_message("❌ La durée doit être supérieure à 0.", ephemeral=True)
            return
        try:
            await member.timeout(timedelta(minutes=minutes), reason=reason)
            await interaction.response.send_message(f"🔇 {member.mention} a été mute pendant {minutes} minutes. Raison : {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Je n’ai pas la permission de mute ce membre.", ephemeral=True)

    # ----------------------------
    # UNMUTE
    # ----------------------------
    @app_commands.command(name="unmute", description="Unmute un membre")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins    
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None)
            await interaction.response.send_message(f"🔊 {member.mention} a été unmute.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Je n’ai pas la permission de unmute ce membre.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Administration(bot))
