import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import json
import os
from datetime import datetime

CONFIG_FILE = "auto_messages.json"

def load_data():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"messages": {}}

def save_data(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class messagecogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()
        self.tasks = {}
        self.restore_tasks()

    # 🔄 Restaurer les tâches après un restart
    def restore_tasks(self):
        for guild_id, messages in self.data["messages"].items():
            for msg_id, info in messages.items():
                self.start_task(guild_id, msg_id, info)

    # 🚀 Lancer une tâche auto-message
    def start_task(self, guild_id, msg_id, info):
        async def task_loop():
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(int(info["channel_id"]))
            if not channel:
                return
            while True:
                embed = discord.Embed(
                    title=info["title"],
                    description=info["description"],
                    color=discord.Color.from_rgb(18, 18, 18),
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text="Message automatique")
                await channel.send(embed=embed)
                await asyncio.sleep(info["interval"])

        self.tasks[msg_id] = self.bot.loop.create_task(task_loop())

    # 🛑 Stopper une tâche
    def stop_task(self, msg_id):
        if msg_id in self.tasks:
            self.tasks[msg_id].cancel()
            del self.tasks[msg_id]

    # 🎛️ Commande principale
    @app_commands.command(name="pannel_message", description="Configurer un message automatique (admin seulement)")
    @app_commands.checks.has_permissions(administrator=True)
    async def pannel_message(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        interval: int,
        title: str,
        description: str
    ):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.data["messages"]:
            self.data["messages"][guild_id] = {}

        msg_id = str(len(self.data["messages"][guild_id]) + 1)

        self.data["messages"][guild_id][msg_id] = {
            "channel_id": str(channel.id),
            "interval": interval * 60,  # minutes → secondes
            "title": title,
            "description": description
        }
        save_data(self.data)

        # Lancer la tâche
        self.start_task(guild_id, msg_id, self.data["messages"][guild_id][msg_id])

        await interaction.response.send_message(
            f"✅ Message automatique ajouté dans {channel.mention} toutes les **{interval} minutes**.",
            ephemeral=True
        )

    # ❌ Supprimer un auto-message
    @app_commands.command(name="remove_message", description="Supprimer un message automatique (admin seulement)")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_message(self, interaction: discord.Interaction, msg_id: str):
        guild_id = str(interaction.guild.id)
        if guild_id in self.data["messages"] and msg_id in self.data["messages"][guild_id]:
            self.stop_task(msg_id)
            del self.data["messages"][guild_id][msg_id]
            save_data(self.data)
            await interaction.response.send_message(f"🗑️ Message automatique **{msg_id}** supprimé.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Aucun message trouvé avec cet ID.", ephemeral=True)

    # 📋 Voir la liste
    @app_commands.command(name="list_messages", description="Voir les messages automatiques configurés (admin seulement)")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_messages(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.data["messages"] or not self.data["messages"][guild_id]:
            await interaction.response.send_message("⚠️ Aucun message automatique configuré.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Messages automatiques",
            color=discord.Color.orange()
        )
        for msg_id, info in self.data["messages"][guild_id].items():
            channel = self.bot.get_channel(int(info["channel_id"]))
            embed.add_field(
                name=f"ID: {msg_id}",
                value=f"Salon: {channel.mention if channel else 'inconnu'}\n"
                      f"Toutes les {info['interval']//60} min\n"
                      f"Titre: {info['title']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(messagecogs(bot))