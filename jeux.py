import discord
from discord.ext import commands
from discord import app_commands
import random

class JeuxCog(commands.Cog):
    """Cog pour jeux : Pierre-Feuille-Ciseaux, Pile-Face et Nombre à deviner"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.leaderboard = {}  # {user_id: victories}

    # -----------------------------
    # Pierre Feuille Ciseaux
    # -----------------------------
    @app_commands.command(name="pierre_feuille_siceaux", description="Joue au Pierre-Feuille-Ciseaux contre un bot ou joueur")
    @app_commands.describe(opponent="Mentionnez un joueur ou laissez vide pour jouer contre le bot")
    async def pfc(self, interaction: discord.Interaction, opponent: discord.Member = None):
        options = ["Pierre", "Feuille", "Ciseaux"]

        if opponent is None or opponent == interaction.user:
            # Contre le bot
            bot_choice = random.choice(options)
            await interaction.response.send_message(f"{interaction.user.mention}, choisissez votre option: Pierre, Feuille ou Ciseaux ?", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel and m.content.capitalize() in options

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=30)
            except:
                await interaction.followup.send("⏰ Temps écoulé !")
                return

            player_choice = msg.content.capitalize()
            result = self.determine_winner(player_choice, bot_choice, interaction.user, "Bot")
            await interaction.followup.send(f"Vous avez choisi {player_choice}, le bot a choisi {bot_choice}.\n{result}")

        else:
            # Contre un autre joueur
            await interaction.response.send_message(f"{interaction.user.mention} défie {opponent.mention} ! Les deux joueurs, envoyez votre choix en MP (Pierre, Feuille, Ciseaux).")

            def check_dm(m):
                return m.author in [interaction.user, opponent] and isinstance(m.channel, discord.DMChannel) and m.content.capitalize() in options

            try:
                choices = {}
                while len(choices) < 2:
                    msg = await self.bot.wait_for("message", check=check_dm, timeout=60)
                    choices[msg.author.id] = msg.content.capitalize()
            except:
                await interaction.followup.send("⏰ Temps écoulé ! Un des joueurs n'a pas répondu.")
                return

            player1_choice = choices[interaction.user.id]
            player2_choice = choices[opponent.id]
            result = self.determine_winner(player1_choice, player2_choice, interaction.user, opponent)
            await interaction.followup.send(f"{interaction.user.display_name} a choisi {player1_choice}, {opponent.display_name} a choisi {player2_choice}.\n{result}")

    # -----------------------------
    # Pile ou Face
    # -----------------------------
    @app_commands.command(name="pileface", description="Joue à pile ou face contre un bot ou joueur")
    @app_commands.describe(opponent="Mentionnez un joueur ou laissez vide pour jouer contre le bot")
    async def pileface(self, interaction: discord.Interaction, opponent: discord.Member = None):
        options = ["Pile", "Face"]

        if opponent is None or opponent == interaction.user:
            bot_choice = random.choice(options)
            await interaction.response.send_message(f"{interaction.user.mention}, choisissez Pile ou Face ?", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel and m.content.capitalize() in options

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=30)
            except:
                await interaction.followup.send("⏰ Temps écoulé !")
                return

            player_choice = msg.content.capitalize()
            result = self.determine_winner(player_choice, bot_choice, interaction.user, "Bot")
            await interaction.followup.send(f"Vous avez choisi {player_choice}, le bot a choisi {bot_choice}.\n{result}")
        else:
            await interaction.response.send_message(f"{interaction.user.mention} défie {opponent.mention} ! Envoyez votre choix en DM (Pile ou Face).")

            def check_dm(m):
                return m.author in [interaction.user, opponent] and isinstance(m.channel, discord.DMChannel) and m.content.capitalize() in options

            try:
                choices = {}
                while len(choices) < 2:
                    msg = await self.bot.wait_for("message", check=check_dm, timeout=60)
                    choices[msg.author.id] = msg.content.capitalize()
            except:
                await interaction.followup.send("⏰ Temps écoulé !")
                return

            player1_choice = choices[interaction.user.id]
            player2_choice = choices[opponent.id]
            result = self.determine_winner(player1_choice, player2_choice, interaction.user, opponent)
            await interaction.followup.send(f"{interaction.user.display_name} a choisi {player1_choice}, {opponent.display_name} a choisi {player2_choice}.\n{result}")

    # -----------------------------
    # Nombre à deviner
    # -----------------------------
    @app_commands.command(name="nombre_a_deviner", description="Devine un nombre entre 1 et 100 contre le bot")
    async def nombre_a_deviner(self, interaction: discord.Interaction):
        number = random.randint(1, 100)
        await interaction.response.send_message(f"{interaction.user.mention}, devinez un nombre entre 1 et 100.", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit()

        attempts = 0
        while True:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except:
                await interaction.followup.send("⏰ Temps écoulé !")
                return
            guess = int(msg.content)
            attempts += 1
            if guess < number:
                await msg.channel.send("📉 Plus grand !")
            elif guess > number:
                await msg.channel.send("📈 Plus petit !")
            else:
                self.leaderboard[interaction.user.id] = self.leaderboard.get(interaction.user.id, 0) + 1
                await msg.channel.send(f"🎉 Bravo {interaction.user.mention}, vous avez trouvé le nombre en {attempts} essais !")
                break

    # -----------------------------
    # Détermination du gagnant
    # -----------------------------
    def determine_winner(self, choice1, choice2, player1, player2):
        if choice1 == choice2:
            return "Égalité !"
        wins = {"Pierre": "Ciseaux", "Ciseaux": "Feuille", "Feuille": "Pierre", "Pile": "Face", "Face": "Pile"}
        if wins[choice1] == choice2:
            self.leaderboard[player1.id] = self.leaderboard.get(player1.id, 0) + 1
            return f"🎉 {player1.display_name} gagne !"
        else:
            winner_name = player2 if isinstance(player2, str) else player2.display_name
            if isinstance(player2, discord.Member):
                self.leaderboard[player2.id] = self.leaderboard.get(player2.id, 0) + 1
            return f"🎉 {winner_name} gagne !"

    # -----------------------------
    # Leaderboard
    # -----------------------------
    @app_commands.command(name="leaderboard_jeux", description="Affiche le leaderboard général des jeux")
    async def leaderboard_jeux(self, interaction: discord.Interaction):
        if not self.leaderboard:
            await interaction.response.send_message("Aucun score pour le moment.", ephemeral=True)
            return

        sorted_lb = sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)
        description = ""
        for idx, (user_id, score) in enumerate(sorted_lb[:10], start=1):
            member = interaction.guild.get_member(user_id)
            name = member.display_name if member else f"ID {user_id}"
            description += f"{idx}) {name} - {score} victoires\n"

        embed = discord.Embed(
            title="🏆 Leaderboard Général",
            description=description,
            color=discord.Color.from_rgb(18, 18, 18)
        )
        await interaction.response.send_message(embed=embed)

# -----------------------------
# Setup du Cog
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(JeuxCog(bot))
