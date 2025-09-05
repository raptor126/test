import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Chargement des cogs + sync dans setup_hook
@bot.event
async def setup_hook():
    # Charger automatiquement tous les cogs du dossier ./cogs
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"🔹 Cog chargé : {filename}")
            except Exception as e:
                print(f"❌ Erreur de chargement du cog {filename}: {e}")

    # Synchroniser les commandes slash
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes slash synchronisées.")
    except Exception as e:
        print(f"❌ Erreur de synchronisation des slash commands : {e}")

@bot.event
async def on_ready():
    print(f"🤖 Connecté en tant que {bot.user} (ID: {bot.user.id})")

async def main():
    async with bot:
        await bot.start("") 

if __name__ == "__main__":
    asyncio.run(main())
