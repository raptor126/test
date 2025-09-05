import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_FILE = "ticket_config.json"

# Charger la config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ======================
# CLASSE POUR LES ACTIONS DANS LE TICKET
# ======================
class TicketActions(discord.ui.View):
    def __init__(self, author: discord.Member, staff_role: discord.Role, log_channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.author = author
        self.staff_role = staff_role
        self.log_channel = log_channel
        self.locked = False
        self.claimed_by = None
        self.lock_reason = None

    # 🔒 Fermer
    @discord.ui.button(label="🔒 Fermer", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author and self.staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Vous n'avez pas la permission de fermer ce ticket.", ephemeral=True)
            return

        messages = [msg async for msg in interaction.channel.history(limit=None, oldest_first=True)]
        transcript = "\n".join(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author}: {msg.content}" for msg in messages)

        if self.log_channel:
            await self.log_channel.send(f"📝 Transcript du ticket {interaction.channel.name}:\n```{transcript}```")

        await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")

    # 🚫 Bloquer
    @discord.ui.button(label="🚫 Bloquer", style=discord.ButtonStyle.secondary)
    async def lock_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Seul le staff peut bloquer le ticket.", ephemeral=True)
            return
        if self.locked:
            await interaction.response.send_message("⚠️ Ce ticket est déjà bloqué.", ephemeral=True)
            return

        # Demander la raison
        await interaction.response.send_modal(LockModal(self))

    # ✅ Débloquer
    @discord.ui.button(label="✅ Débloquer", style=discord.ButtonStyle.success)
    async def unlock_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Seul le staff peut débloquer le ticket.", ephemeral=True)
            return
        if not self.locked:
            await interaction.response.send_message("⚠️ Ce ticket n'est pas bloqué.", ephemeral=True)
            return

        self.locked = False
        self.lock_reason = None
        await interaction.channel.set_permissions(self.author, send_messages=True)
        embed = discord.Embed(
            title="✅ Ticket débloqué",
            description=f"Le ticket a été débloqué par {interaction.user.mention}. Vous pouvez à nouveau parler.",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed)

    # 🙋 Claim
    @discord.ui.button(label="🙋 Claim", style=discord.ButtonStyle.blurple)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Seul le staff peut claim ce ticket.", ephemeral=True)
            return
        if self.claimed_by:
            await interaction.response.send_message(f"⚠️ Ce ticket est déjà claim par {self.claimed_by.mention}.", ephemeral=True)
            return

        self.claimed_by = interaction.user
        embed = discord.Embed(
            title="🙋 Ticket Claim",
            description=f"{interaction.user.mention} a claim ce ticket, il s’en occupe.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

# ======================
# MODAL POUR LA RAISON DU LOCK
# ======================
class LockModal(discord.ui.Modal, title="Raison du blocage"):
    reason = discord.ui.TextInput(label="Raison du blocage", style=discord.TextStyle.paragraph, required=False, max_length=200)

    def __init__(self, ticket_view: TicketActions):
        super().__init__()
        self.ticket_view = ticket_view

    async def on_submit(self, interaction: discord.Interaction):
        self.ticket_view.locked = True
        self.ticket_view.lock_reason = self.reason.value or "Aucune raison fournie"
        await interaction.channel.set_permissions(self.ticket_view.author, send_messages=False)
        embed = discord.Embed(
            title="🚫 Ticket bloqué",
            description=f"Ce ticket a été bloqué par {interaction.user.mention}.\n**Raison :** {self.ticket_view.lock_reason}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

# ======================
# SELECT POUR CHOISIR LE TYPE DE TICKET
# ======================
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="--Avis--", value="avis", description="Avis payer"),
            discord.SelectOption(label="--Achat--", value="achat", description="Achat"),
            discord.SelectOption(label="--Question--", value="question", description="Demander de l'aide"),
        ]
        super().__init__(placeholder="Choisis un type de ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_config = config.get(guild_id, {})

        if not guild_config.get("categories") or not guild_config.get("staff_role") or not guild_config.get("log_channel"):
            await interaction.response.send_message("⚠️ Le système de tickets n'est pas configuré correctement.", ephemeral=True)
            return

        category_id = guild_config["categories"].get(self.values[0])
        if not category_id:
            await interaction.response.send_message(f"⚠️ La catégorie pour ce ticket n'est pas définie.", ephemeral=True)
            return

        category = interaction.guild.get_channel(category_id)
        staff_role = interaction.guild.get_role(guild_config["staff_role"])
        log_channel = interaction.guild.get_channel(guild_config["log_channel"])

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True)
        }

        ticket_channel = await interaction.guild.create_text_channel(
            name=f"{self.values[0]}-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎟️ Ticket {self.values[0].capitalize()} ouvert",
            description=f"{interaction.user.mention} a ouvert un ticket.\n{staff_role.mention} va te répondre bientôt !",
            color=discord.Color.from_rgb(18, 18, 18)
        )

        view = TicketActions(interaction.user, staff_role, log_channel)
        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket créé : {ticket_channel.mention}", ephemeral=True)

# ======================
# VIEW DU PANNEAU
# ======================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TicketSelect())

# ======================
# COG PRINCIPAL
# ======================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pannel_ticket", description="Configurer le système de tickets et envoyer le panneau")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        category_avis="Catégorie pour les tickets Avis",
        category_achat="Catégorie pour les tickets Achat",
        category_question="Catégorie pour les tickets Question",
        staff_role="Rôle du staff",
        log_channel="Salon de logs des tickets",
        media="Image ou vidéo optionnelle à afficher dans le panneau"
    )
    async def pannel_ticket(
        self,
        interaction: discord.Interaction,
        category_avis: discord.CategoryChannel,
        category_achat: discord.CategoryChannel,
        category_question: discord.CategoryChannel,
        staff_role: discord.Role,
        log_channel: discord.TextChannel,
        media: discord.Attachment = None
    ):
        guild_id = str(interaction.guild.id)
        config[guild_id] = config.get(guild_id, {})
        config[guild_id]["staff_role"] = staff_role.id
        config[guild_id]["log_channel"] = log_channel.id
        config[guild_id]["categories"] = {}
        config[guild_id]["categories"]["avis"] = category_avis.id
        config[guild_id]["categories"]["achat"] = category_achat.id
        config[guild_id]["categories"]["question"] = category_question.id

        if media:
            config[guild_id]["media_url"] = media.url
            config[guild_id]["media_type"] = media.content_type
        else:
            config[guild_id]["media_url"] = None
            config[guild_id]["media_type"] = None

        save_config()

        embed = discord.Embed(
            title="🎟️ Panneau de Tickets",
            description="Choisis un type de ticket ci-dessous :",
            color=discord.Color.from_rgb(18, 18, 18)
        )

        if media:
            if media.content_type.startswith("image/"):
                embed.set_image(url=media.url)
            else:
                embed.add_field(name="📎 Média", value=f"[Voir le fichier]({media.url})", inline=False)

        view = TicketView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Panneau et configuration enregistrés !", ephemeral=True)

    @app_commands.command(name="ticket", description="Ouvrir le panneau de tickets")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def ticket(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_config = config.get(guild_id, {})

        if not guild_config.get("categories"):
            await interaction.response.send_message("⚠️ Le système de tickets n'est pas configuré correctement.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎟️ Panneau de Tickets",
            description="Choisis un type de ticket ci-dessous :",
            color=discord.Color.from_rgb(18, 18, 18)
        )

        media_url = guild_config.get("media_url")
        media_type = guild_config.get("media_type")
        if media_url:
            if media_type and media_type.startswith("image/"):
                embed.set_image(url=media_url)
            else:
                embed.add_field(name="📎 Média", value=f"[Voir le fichier]({media_url})", inline=False)

        view = TicketView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
