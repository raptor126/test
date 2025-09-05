import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json, os

CONFIG_FILE = "antipub.json"

def load_data():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"enabled_guilds": [], "warnings": {}, "muted_until": {}}

def save_data(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

class banliencogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()
        # Convert muted_until strings en datetime
        for guild_id in self.data["muted_until"]:
            for user_id in list(self.data["muted_until"][guild_id].keys()):
                try:
                    self.data["muted_until"][guild_id][user_id] = datetime.fromisoformat(
                        self.data["muted_until"][guild_id][user_id]
                    )
                except:
                    del self.data["muted_until"][guild_id][user_id]

    def is_enabled(self, guild_id: int) -> bool:
        return str(guild_id) in self.data["enabled_guilds"]

    @app_commands.command(name="banlien", description="Active/Désactive le système anti-lien (admin seulement)")
    @app_commands.checks.has_permissions(administrator=True)
    async def banlien(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id in self.data["enabled_guilds"]:
            self.data["enabled_guilds"].remove(guild_id)
            save_data(self.data)
            await interaction.response.send_message("🚫 Le système anti-lien a été **désactivé**.", ephemeral=True)
        else:
            self.data["enabled_guilds"].append(guild_id)
            save_data(self.data)
            await interaction.response.send_message("✅ Le système anti-lien a été **activé**.", ephemeral=True)

    # Event : message envoyé
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        guild = message.guild
        if not guild or not self.is_enabled(guild.id):
            return

        if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
            if message.author.guild_permissions.administrator:
                return

            await message.delete()
            await message.channel.send(
                f"⚠️ {message.author.mention}, merci de ne pas envoyer de lien d'autre serveur ici !",
                delete_after=5
            )

            guild_id = str(guild.id)
            user_id = str(message.author.id)

            if guild_id not in self.data["warnings"]:
                self.data["warnings"][guild_id] = {}
            if user_id not in self.data["warnings"][guild_id]:
                self.data["warnings"][guild_id][user_id] = 0

            self.data["warnings"][guild_id][user_id] += 1
            warn_count = self.data["warnings"][guild_id][user_id]
            save_data(self.data)

            if warn_count >= 3:
                mute_role = discord.utils.get(guild.roles, name="Muted")
                if not mute_role:
                    mute_role = await guild.create_role(name="Muted", reason="Rôle automatique anti-pub")
                    for channel in guild.channels:
                        await channel.set_permissions(mute_role, send_messages=False, speak=False, add_reactions=False)

                await message.author.add_roles(mute_role, reason="3 avertissements anti-pub")
                mute_time = datetime.utcnow() + timedelta(hours=1)

                if guild_id not in self.data["muted_until"]:
                    self.data["muted_until"][guild_id] = {}
                self.data["muted_until"][guild_id][user_id] = mute_time.isoformat()

                self.data["warnings"][guild_id][user_id] = 0  # reset warnings après mute
                save_data(self.data)

                await message.channel.send(f"🔇 {message.author.mention} a été **muté 1h** pour spam de liens Discord.")

    @tasks.loop(minutes=1)
    async def check_unmute(self):
        now = datetime.utcnow()
        for guild_id, users in list(self.data["muted_until"].items()):
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue
            for user_id, until_str in list(users.items()):
                try:
                    until = datetime.fromisoformat(until_str) if isinstance(until_str, str) else until_str
                except:
                    continue

                if now >= until:
                    member = guild.get_member(int(user_id))
                    if member:
                        mute_role = discord.utils.get(guild.roles, name="Muted")
                        if mute_role in member.roles:
                            await member.remove_roles(mute_role, reason="Fin du mute auto")
                            print(f"✅ {member} a été unmute automatiquement")
                    del self.data["muted_until"][guild_id][user_id]
                    save_data(self.data)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_unmute.is_running():
            self.check_unmute.start()

async def setup(bot: commands.Bot):
    await bot.add_cog(banliencogs(bot))
