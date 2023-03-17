import datetime
import json
import os
import random
import time
import traceback
from typing import Literal
import discord
from discord.ext import commands
import aiosqlite3
import pyttsx3
from cogs.hyperlands.functions import set_win, set_loss, cooldown

class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Closed!", ephemeral=True)
        await interaction.channel.delete()

class HyperLandsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    scrims = discord.app_commands.Group(
    name="scrims",
    description="...",
    guild_ids=[int(os.getenv("MAIN_GUILD"))]
)


    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.log("cogs.hyperlands.win is now ready!")

    @scrims.command(
        name="win",
        description="Marks the specified game as won."
    )
    @discord.app_commands.describe(team="The team that won the scrim.")
    @discord.app_commands.checks.has_role(os.getenv("SCRIM_SCORER_ROLE_NAME"))
    async def _win(self, interaction: discord.Interaction, team: Literal['Team 1', 'Team 2']):
        await interaction.response.defer()
        
        conn = self.bot.conn 
        cursor = await conn.cursor()
        await cursor.execute('SELECT * FROM hyperlands WHERE channel_id = ?', (interaction.channel.id,))
        data = await cursor.fetchone()

        if not data:
            embed = discord.Embed(
                description="This isn't a scrim channel! This command can only be used in a scrim channel. Please use this command in a scrim channel.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name="Error", icon_url=self.bot.user.avatar.url)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return await interaction.edit_original_response(embed=embed)

        if not data[8]:
            return await interaction.edit_original_response(content=f":x: This scrim has not started yet! Please wait for the scrim to start before ending it.")

        if data[12] == "end":
            await interaction.edit_original_response(content=f":x: This scrim has already ended!")
            return
        
        if team == "Team 1":
            team1 = [interaction.guild.get_member(int(player)) for player in json.loads(data[8])]
            team2 = [interaction.guild.get_member(int(player)) for player in json.loads(data[9])]
            await set_win(team1)
            await set_loss(team2)
            await cursor.execute("UPDATE hyperlands SET winner = ?, status = ? WHERE channel_id = ?", (1, "end", interaction.channel.id))
            await conn.commit()
            await cursor.close()
            hyper_game_logs = self.bot.get_channel(int(os.getenv("GAME_LOGS")))
                    
            winnerMentions = [member.mention for member in team1]

            embed = discord.Embed(
                title=f"Scrim#{interaction.channel.name.split('-')[-1]}",
                description=f"Scrim has eneded. \nWinners: {', '.join(winnerMentions)}\nLosers: {', '.join([member.mention for member in team2])}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )

            await hyper_game_logs.send(embed=embed)
            await interaction.edit_original_response(content=":white_check_mark: Team 1 has won the scrim! ELO will be given shortly.")
            return
        elif team == "Team 2":
            team1 = [interaction.guild.get_member(int(player)) for player in json.loads(data[8])]
            team2 = [interaction.guild.get_member(int(player)) for player in json.loads(data[9])]
            await set_win(team2)
            await set_loss(team1)
            await cursor.execute("UPDATE hyperlands SET winner = ?, status = ? WHERE channel_id = ?", (2, "end", interaction.channel.id))
            await conn.commit()
            await cursor.close()
            hyper_game_logs = self.bot.get_channel(int(os.getenv("GAME_LOGS")))

            winnerMentions = [member.mention for member in team2]

            embed = discord.Embed(
                title=f"Scrim#{interaction.channel.name.split('-')[-1]}",
                description=f"Scrim has eneded. \nWinners: {', '.join(winnerMentions)}\nLosers: {', '.join([member.mention for member in team1])}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )

            await hyper_game_logs.send(embed=embed)
            await interaction.edit_original_response(content=":white_check_mark: Team 2 has won the scrim! ELO will be given shortly.")
            return

    @_win.error
    async def _win_error_handler(self, interaction: discord.Interaction, error: Exception):
        if isinstance(error, discord.app_commands.errors.MissingRole):
            embed = discord.Embed(
                description="You don't have the required role to use this command! If you wish to mark this game as won, please contact a Scorer.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name="Error", icon_url=self.bot.user.avatar.url)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return await interaction.edit_original_response(embed=embed)
        else:
            await interaction.edit_original_response(content=f":x: An error has occured: {error}" )
            traceback.print_exc()

    elo = discord.app_commands.Group(
        name="elo",
        description="...",
        parent=scrims,
        guild_ids=[int(os.getenv("MAIN_GUILD"))]
    )

    @elo.command(
        name="change",
        description="Manually gives elo to a user."
    ) 
    @discord.app_commands.checks.has_role(os.getenv("SCRIM_SCORER_ROLE_NAME"))
    async def _add_elo(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await interaction.response.defer()
        conn = self.bot.conn 
        cursor = await conn.cursor()

        await cursor.execute(f"SELECT * FROM playersElo WHERE id = (?)", (member.id,))

        data = await cursor.fetchone()

        if not data:
            await cursor.execute("INSERT INTO playersElo VALUES (?, ?, ?, ?, ?, ?, ?)", (member.id, member.name, 0, 0, 0, 0, 0))
            await conn.commit()
        
        await cursor.execute(f"SELECT * FROM playersElo WHERE id = (?)", (member.id,))
        data = await cursor.fetchone()
        elo = data[2]
        elo = amount
        await cursor.execute(f"UPDATE playersElo SET elo = (?) WHERE id = (?)", (elo, member.id))
        await conn.commit()
        await cursor.close()

        try:
            await member.edit(nick=f"{elo} | {member.name}")
        except:
            pass

        await interaction.edit_original_response(content=f"Successfully changed `{member}`'s elo to {amount}!")

    @_add_elo.error
    async def _add_elo_error_handler(self, interaction: discord.Interaction, error: Exception):
        if isinstance(error, discord.app_commands.errors.MissingRole):
            embed = discord.Embed(
                description="You don't have the required role to use this command. If you wish to change your elo, please contact an administrator.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name="Error", icon_url=self.bot.user.avatar.url)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return await interaction.edit_original_response(embed=embed)
        else:
            await interaction.response.send_message(content=f":x: An error has occured: {error}" )
            traceback.print_exc()

    quick_fold = discord.app_commands.Group(
        name="quick",
        description="...",
        parent=scrims,
        guild_ids=[int(os.getenv("MAIN_GUILD"))]
    )

    @quick_fold.command(
        name="fold",
        description="Quickly folds a scrim, 100 ELO loss penalty."
    )
    async def _quick_fold(self, interaction: discord.Interaction):
        await interaction.response.defer()

        conn = self.bot.conn 
        cursor = await conn.cursor()
        await cursor.execute(f"SELECT * FROM hyperlands WHERE channel_id = (?)", (interaction.channel.id,))
        data = await cursor.fetchone()
        if not data:
            embed = discord.Embed(
                description="This isn't a scrim channel! This command can only be used in a scrim channel. Please use this command in a scrim channel.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name="Error", icon_url=self.bot.user.avatar.url)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return await interaction.edit_original_response(embed=embed)
        
        players = []
        for i, player in enumerate(data):
            if i > 7:
                break
            players.append(int(player))
        
        for player in players:
            await cursor.execute(f"SELECT * FROM playersElo WHERE id = (?)", (player,))
            data = await cursor.fetchone()
            if not data:
                await cursor.execute("INSERT INTO playersElo VALUES (?, ?, ?, ?, ?, ?, ?)", (player, interaction.guild.get_member(player).name, 0, 0, 0, 0, 0))
                await conn.commit()
                member = interaction.guild.get_member(player)
                await member.edit(nick=f"{newElo} | {data[1]}")
            else:
                newElo = data[2] - 100
                if newElo < 0: newElo = 9
                await cursor.execute(f"UPDATE playersElo SET elo = (?) WHERE id = (?)", (newElo, player))
                member = interaction.guild.get_member(player)
                await member.edit(nick=f"{newElo} | {data[1]}")

        embed = discord.Embed(
            description="100 ELO has been deducted from each player. This game will be deleted in 5 seconds."
        )
        await interaction.edit_original_response(embed=embed)

    @_quick_fold.error
    async def _quick_fold_error_handler(self, interaction: discord.Interaction, error: Exception):
        if isinstance(error, discord.app_commands.errors.MissingRole):
            embed = discord.Embed(
                description="You don't have the required role to use this command. If you wish to change your elo, please contact an administrator.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name="Error", icon_url=self.bot.user.avatar.url)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return await interaction.edit_original_response(embed=embed)
        else:
            await interaction.response.send_message(content=f":x: An error has occured: {error}" )
            traceback.print_exc()

    @scrims.command(
        name="ping",
        description="Pings for a scrim. Can be only used every 25 minutes."
    )
    @discord.app_commands.commands.guild_only()
    @discord.app_commands.checks.cooldown(1, 1500.0, key=None)
    async def _ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel = interaction.guild.get_channel(int(os.getenv("HYPER_SCRIM_CHANNEL")))
        await channel.send(interaction.guild.get_role(int(os.getenv("SCRIM_ROLE"))).mention)
        await interaction.edit_original_response(content=":white_check_mark: Pinged!")

    @_ping.error
    async def _ping_error_handler(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.defer()
        if isinstance(error, discord.app_commands.errors.CommandOnCooldown):
            time_left = str(error)
            time_left = time_left.split(" ")[-1]
            time_left = time_left.split(".")[0]
            time_left = int(time_left)
            embed = discord.Embed(
                description=f"This comamnd is currently on cooldown! Please try again in {round(time_left/60)} minute(s).",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name="Error", icon_url=self.bot.user.avatar.url)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return await interaction.edit_original_response(embed=embed)
        else:
            await interaction.edit_original_response(content=f":x: An error has occured: {error}" )
            traceback.print_exc()

    @scrims.command(
        name="move",
        description=f"Moves a user to a different voice channel."
    )
    async def _move(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            return await interaction.edit_original_response(content=":x: You are not in a voice channel! Please tell them to join a voice channel first.")
        
        if not member.voice:
            return await interaction.edit_original_response(content=":x: The member is not in a voice channel! Please tell them to join a voice channel first.")

        await member.move_to(interaction.user.voice.channel)
        await interaction.edit_original_response(content=f":white_check_mark: Moved `{member}` to {interaction.user.voice.channel.mention}`!")

    @scrims.command(
        name="report",
        description=f"Report a user for cheating."
    )
    async def _report(self, interaction: discord.Interaction, member: discord.Member, evidence: discord.Attachment = None):
        await interaction.response.defer(ephemeral=True)
        
        if member == interaction.user:
            return await interaction.edit_original_response(content=":x: You can't report yourself!")
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await interaction.guild.create_text_channel(
            name=f"report-{interaction.user}",
            overwrites=overwrites,
            reason="Report channel"
        )

        embed = discord.Embed(
            description=f"{interaction.user} has created a report channel for {member.mention}.",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name="Report", icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        evidence = await evidence.to_file()

        if evidence:
            await channel.send(files=[evidence], embed=embed, view=CloseButton(), content=interaction.user.mention)
        else:
            await channel.send(embed=embed, view=CloseButton(), content=interaction.user.mention)

        await interaction.edit_original_response(content=f":white_check_mark: Successfully created a report channel, {channel.mention}!")
        
    @scrims.command(
        name="sub",
        description="Subs a player for another player"
    )
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def _sub(self, interaction: discord.Interaction, player1: discord.Member, player2: discord.Member):
        await interaction.response.defer()

        # conn = await aiosqlite3.connect("db.db")
        # cursor = await conn.cursor()

        # await cursor.execute("SELECT * FROM hyperlands WHERE channel_id = ?", (interaction.channel.id,))
        # data = await cursor.fetchone()
        # if not data:
        #     return await interaction.edit_original_response(content=":x: This channel is not a scrim channel!")
        
        # if data:
        #     await cursor.execute("UPDATE hyperlands WHERE channe_id = (?) SET ")

        await interaction.edit_original_response(content=":x: This command is currently in development.")

    @scrims.command(
        name="ban",
        description="Bans a player from scrims."
    )
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def _ban(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()

        role = interaction.guild.get_role(int(os.getenv("BAN_SCRIM_ROLE")))
        await member.add_roles(role)

        await interaction.edit_original_response(content=f":white_check_mark: Successfully banned {member.mention} from scrims!")

    @scrims.command(
        name="unban",
        description="Unbans a player from scrims."
    )
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def _unban(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()

        role = interaction.guild.get_role(int(os.getenv("BAN_SCRIM_ROLE")))
        if not member.get_role(role.id):
            return await interaction.edit_original_response(content=f":x: {member.mention} is not banned from scrims!")

        await member.remove_roles(role)
        await interaction.edit_original_response(content=f":white_check_mark: Successfully unbanned {member.mention} from scrims!")

    @discord.app_commands.command(
        name="tts",
        description="Sends a message in tts."
    )
    @discord.app_commands.guilds(int(os.getenv("MAIN_GUILD")))
    async def _tts(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            return await interaction.edit_original_response(content=":x: You are not in a voice channel! Please join a voice channel first.")

        engine = pyttsx3.init()
        engine.save_to_file(message , 'test.mp3')
        engine.runAndWait()

        await interaction.user.voice.channel.connect()
        interaction.client.voice_clients[0].play(discord.FFmpegPCMAudio("test.mp3"))
        await interaction.edit_original_response(content=f":white_check_mark: Successfully sent a tts message in {interaction.user.voice.channel.mention}!")
        os.remove("test.mp3")

async def setup(bot: commands.Bot):
    await bot.add_cog(HyperLandsCommands(bot))