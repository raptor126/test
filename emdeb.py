import discord
from discord.ext import commands
from discord import app_commands

class EmbedEditor(discord.ui.View):
    def __init__(self, embed: discord.Embed, author_id: int):
        super().__init__(timeout=600)
        self.embed = embed
        self.author_id = author_id
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Vous ne pouvez pas modifier cet embed.", ephemeral=True)
            return False
        return True

    # Modifier le titre
    @discord.ui.button(label="📝 Modifier le titre", style=discord.ButtonStyle.primary)
    async def edit_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✏️ Entrez le **nouveau titre** :", ephemeral=True)

        def check(m): return m.author.id == self.author_id and m.channel == interaction.channel
        msg = await interaction.client.wait_for("message", check=check)

        self.embed.title = msg.content
        await self.message.edit(embed=self.embed)
        await msg.delete()

    # Modifier la description
    @discord.ui.button(label="📜 Modifier la description", style=discord.ButtonStyle.primary)
    async def edit_desc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✏️ Entrez la **nouvelle description** :", ephemeral=True)

        def check(m): return m.author.id == self.author_id and m.channel == interaction.channel
        msg = await interaction.client.wait_for("message", check=check)

        self.embed.description = msg.content
        await self.message.edit(embed=self.embed)
        await msg.delete()

    # Ajouter image / vidéo
    @discord.ui.button(label="🖼️ Ajouter image/vidéo", style=discord.ButtonStyle.secondary)
    async def add_media(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📸 Envoyez une **image ou vidéo** de votre galerie :", ephemeral=True)

        def check(m): 
            return m.author.id == self.author_id and m.channel == interaction.channel and m.attachments

        msg = await interaction.client.wait_for("message", check=check)
        file = msg.attachments[0]
        file_url = file.url

        # Si c'est une image → affichée dans l'embed
        if file.content_type and file.content_type.startswith("image"):
            self.embed.set_image(url=file_url)
            await self.message.edit(embed=self.embed)

        # Si c'est une vidéo → jointe dans le même message que l'embed
        elif file.content_type and file.content_type.startswith("video"):
            self.embed.set_image(url=None)  # supprime une éventuelle image
            await self.message.edit(embed=self.embed, attachments=[await file.to_file()])

        else:
            await interaction.channel.send("❌ Format non supporté. Envoie une image (.png/.jpg/.gif) ou une vidéo (.mp4/.mov).", delete_after=5)

        await msg.delete()

    # Changer la couleur
    @discord.ui.button(label="🎨 Changer la couleur", style=discord.ButtonStyle.success)
    async def change_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎨 Donnez une couleur hexadécimale (ex: `#ff0000`):", ephemeral=True)

        def check(m): return m.author.id == self.author_id and m.channel == interaction.channel
        msg = await interaction.client.wait_for("message", check=check)

        try:
            color = discord.Color(int(msg.content.strip("#"), 16))
            self.embed.color = color
            await self.message.edit(embed=self.embed)
        except:
            await interaction.channel.send("❌ Couleur invalide. Exemple valide : `#3498db`", delete_after=5)

        await msg.delete()

    # Terminer l'édition
    @discord.ui.button(label="✅ Terminer", style=discord.ButtonStyle.danger)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Édition terminée.", ephemeral=True)

        # Envoie un nouvel embed final sans le panneau
        await interaction.channel.send(embed=self.embed)

        # Désactive les boutons
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)


class EmbedCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Créer et éditer un embed personnalisé")
    @app_commands.default_permissions(administrator=True)
    async def embed(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Titre par défaut",
            description="Description par défaut",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Créé par {interaction.user.display_name}")

        view = EmbedEditor(embed, interaction.user.id)
        msg = await interaction.channel.send(embed=embed, view=view)
        view.message = msg

        await interaction.response.send_message("✅ Embed créé ! Utilisez les boutons pour le modifier.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedCog(bot))