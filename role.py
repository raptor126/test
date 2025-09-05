from discord.ext import commands
from discord import app_commands
import discord

# Variables globales pour stocker le rôle choisi
AUTO_ROLE_ID = None

class RoleSelect(discord.ui.View):
    def __init__(self, roles, bot):
        super().__init__(timeout=None)
        self.bot = bot

        # Ajout du menu déroulant
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles if role < roles[0].guild.me.top_role  # éviter les rôles au-dessus du bot
        ]
        self.add_item(RoleDropdown(options, bot))

class RoleDropdown(discord.ui.Select):
    def __init__(self, options, bot):
        super().__init__(placeholder="Choisis un rôle à attribuer automatiquement", options=options)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        global AUTO_ROLE_ID
        AUTO_ROLE_ID = int(self.values[0])  # Stocke l'ID du rôle choisi
        role = interaction.guild.get_role(AUTO_ROLE_ID)

        # Donne le rôle à tous les membres existants
        for member in interaction.guild.members:
            if not member.bot and role not in member.roles:
                await member.add_roles(role)

        await interaction.response.send_message(
            f"✅ Le rôle **{role.name}** a été sélectionné ! Il sera attribué à chaque nouveau membre et appliqué à tous les membres existants.",
            ephemeral=True
        )

class Rolecogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        global AUTO_ROLE_ID
        if AUTO_ROLE_ID:
            role = member.guild.get_role(AUTO_ROLE_ID)
            if role:
                await member.add_roles(role)

    @app_commands.command(name="pannel_role", description="Choisir un rôle auto-assigné")
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    async def pannel_role(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            roles = [role for role in interaction.guild.roles if role != interaction.guild.default_role]
            view = RoleSelect(roles, self.bot)
            await interaction.response.send_message("🎭 Choisis un rôle à attribuer automatiquement :", view=view)
        else:
            await interaction.response.send_message(
                "❌ Tu n'as pas les permissions nécessaires pour utiliser cette commande.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Rolecogs(bot))
