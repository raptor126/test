import discord
from discord.ext import commands
from discord import app_commands

# Définition de la classe ReactionCog qui contient la commande pour ajouter une réaction
class ReactionCog(commands.Cog):
    
    # Constructeur de la classe, ici on lie le bot à la classe
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Définition de la commande slash /reaction avec une description
    @app_commands.command(name="reaction", description="Ajouter une réaction à un message")
    
    # Vérification des permissions : seuls les utilisateurs ayant la permission "manage_messages" peuvent utiliser cette commande
    @app_commands.default_permissions(administrator=True)  # ✅ visible que pour les admins
    async def reaction(self, interaction: discord.Interaction, message_id: str, emoji: str):
        """
        Fonction qui permet d'ajouter une réaction sur un message spécifique.
        Prend en paramètre l'ID du message et l'emoji à ajouter.
        """
        try:
            # Tentative de récupération du message par son ID dans le salon actuel
            message = await interaction.channel.fetch_message(int(message_id))
        except discord.NotFound:
            # Si le message n'existe pas
            await interaction.response.send_message("❌ Message introuvable. Vérifie l'ID.", ephemeral=True)
            return
        except discord.Forbidden:
            # Si le bot n'a pas la permission de lire les messages dans ce salon
            await interaction.response.send_message("❌ Je n'ai pas la permission de lire ce message.", ephemeral=True)
            return
        except discord.HTTPException as e:
            # Gestion de toute autre erreur HTTP
            await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)
            return

        try:
            # Tentative d'ajout de la réaction à ce message
            await message.add_reaction(emoji)
            # Envoi de la confirmation que la réaction a été ajoutée
            await interaction.response.send_message(f"✅ Réaction {emoji} ajoutée au message {message.jump_url}", ephemeral=True)
        except discord.HTTPException:
            # Si l'emoji est invalide ou que l'ajout échoue
            await interaction.response.send_message("❌ Emoji invalide ou impossible à utiliser.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionCog(bot))
