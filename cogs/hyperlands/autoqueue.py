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

class Autoqueue(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.log("cogs.hyperlands.autoqueue is now ready!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not after.channel:
            print("no after channel")
            return
        if after.channel.id == int(os.getenv("HYPER_QUEUE_CHANNEL")):
            print("after channel is the right one")
            role = member.get_role(os.getenv("BAN_SCRIM_ROLE"))
            if role:
                await member.disconnect()
            if before.channel:
                print("before.channel exists")
                if before.channel.id != int(os.getenv("HYPER_QUEUE_CHANNEL")):
                    print("before.channel isn't the current one (good thing)")
                    pass
                else:
                    print("before.channel is the right one (bad thing)")
                    return
            if len(after.channel.members) != 8:
                if len(after.channel.members) < 8:
                    return
                if len(after.channel.members) > 8:
                    await member.move_to(None, reason="Too many players in the queue.")
                    try:
                        await member.send(f":x: There are too many players in the queue. Please wait until there are 8 players in the queue.")
                    except:
                        pass
                    return
            if len(after.channel.members) == 8:
                    overwrites = {
                        member.guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True, speak=False, connect=False),
                        after.channel.members[0]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[1]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[2]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[3]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[4]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[5]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[6]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[7]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True)
                    }
                    txtOverwrites = {
                        member.guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=False, speak=False, connect=False),
                        after.channel.members[0]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[1]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[2]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[3]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[4]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[5]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[6]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True),
                        after.channel.members[7]: discord.PermissionOverwrite(send_messages=True, view_channel=True, speak=True, connect=True)
                    }

                    category = self.bot.get_channel(int(os.getenv("HYPER_GAMES_CATEGORY")))

                    conn = self.bot.conn("db.db")
                    cursor = await conn.cursor()

                    await cursor.execute("SELECT * FROM count")
                    count = await cursor.fetchone()
                    await cursor.execute("UPDATE count SET num = ?", (count[0] + 1,))
                    await conn.commit()
                    await cursor.close()
                    txt = await category.create_text_channel(
                        name=f"game-{count[0]}",
                        reason="Scrim Channel",
                        overwrites=txtOverwrites
                    )
                    vc1 = await category.create_voice_channel(
                        name=f"game-{count[0]}-Team Select",
                        reason="Scrim Channel",
                        overwrites=overwrites
                    )
                    vc2 = await category.create_voice_channel(
                        name=f"game-{count[0]}-Team 1",
                        reason="Scirm Channel",
                        overwrites=overwrites
                    )
                    vc3 = await category.create_voice_channel(
                        name=f"game-{count[0]}-Team 2",
                        reason="Scirm Chanel",
                        overwrites=overwrites
                    )

                    players = [player.id for player in after.channel.members]

                    tempPlayers = players.copy()

                    t1c = random.choice(tempPlayers)

                    tempPlayers.remove(t1c)

                    t2c = random.choice(tempPlayers)

                    del tempPlayers

                    for member in after.channel.members:
                        await member.move_to(vc1)

                    embed = discord.Embed(
                        title="Team Picking",
                        description=f"2 random captains have been picked for each team. The captains are: \nTeam 1: <@!{t1c}>\nTeam 2: <@!{t2c}>",
                        color=discord.Color.red()
                    )

                    conn = self.bot.conn("db.db")
                    cursor = await conn.cursor()
                    await cursor.execute(
                        """INSERT INTO hyperlands VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (players[0], players[1], players[2], players[3], players[4], players[5], players[6], players[7], "None", "None", t1c, t2c, "start", txt.id, vc1.id, vc2.id, vc3.id, str(time.time()), 0, "None")
                    )

                    await conn.commit()
                    #add to database, replace None with "None"
                    
                    # await cursor.execute(
                    #     """INSERT INTO hyperlands VALUES (?, ?, ?, ?, ?, ?, ?, ?""", (after.channel.members[0], after.channel.members[1], after.channel.members[2], after.channel.members[3], after.channel.members[4], after.channel.members[5], after.channel.members[6], after.channel.members[7], "None", "None", t1c, t2c, "start", txt.id, vc1.id, vc2.id, vc3.id, str(time.time()), 0, "None"), 
                    # )
                    await txt.send(embed=embed)

                    hyper_game_logs = self.bot.get_channel(int(os.getenv("GAME_LOGS")))
                    
                    memberMentions = [member.mention for member in after.channel.members]

                    embed = discord.Embed(
                        title=f"Scrim#{count[0]}",
                        description=f"New scrim has been started. \nMembers: {', '.join(memberMentions)}",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.now()
                    )

                    await hyper_game_logs.send(embed=embed)

                    team1 = []
                    team2 = []

                    team1.append(t1c)
                    team2.append(t2c)

                    def check(message: discord.Message):
                        if message.author.id == t1c:
                            if message.reference:
                                if message.reference.cached_message == msg:
                                    return True
                        return False

                    def check2(message: discord.Message):
                        if message.author.id == t2c:
                            if message.reference:
                                if message.reference.cached_message == msg:
                                    return True
                        return False

                    for i in range(3):
                        msg = await txt.send(f"<@!{t1c}> Please reply to this message with @member you want to pick.")
                        
                        while True:
                            try:
                                msgg = await self.bot.wait_for("message", check=check)
                                if msgg.mentions is None:
                                    await msgg.reply("No member mentioned, try again")
                                    continue
                                if msgg.mentions[1].id in team1 or msgg.mentions[1].id in team2:
                                    await msgg.reply("This member is already picked, try again")
                                    continue
                                elif msgg.mentions[1].id in players:
                                    team1.append(msgg.mentions[1].id)
                                    break
                            except:
                                continue
                        print(team1)
                        print(team2)

                        msg = await txt.send(f"<@!{t2c}> Please reply to this message with @member you want to pick.")
        
                        while True:
                            try:
                                msggg = await self.bot.wait_for("message", check=check2)
                                if msggg.mentions is None:
                                    await msggg.reply("No member mentioned, try again")
                                    continue
                                if msggg.mentions[1].id in team1 or msggg.mentions[1].id in team2:
                                    await msggg.reply("This member is already picked, try again")
                                    continue
                                elif msgg.mentions[1].id in players:
                                    team2.append(msggg.mentions[1].id)
                                    break
                            except:
                                continue

                    team1_to_store = json.dumps(team1)
                    team2_to_store = json.dumps(team2)
                    print(team1_to_store)
                    print(team2_to_store)

                    await cursor.execute(f"UPDATE hyperlands SET t1 = (?) WHERE channel_id = (?)", (team1_to_store, txt.id))

                    await cursor.execute(f"UPDATE hyperlands SET t2 = (?) WHERE channel_id = (?)", (team2_to_store, txt.id))

                    await conn.commit()
                    

                    nl = '\n'
                    embed = discord.Embed(
                        title="Teams Done!",
                        description=f"The teams are done and are shown below:\nTeam 1\n{', '.join('<@!'+str(player)+'>' for player in team1)}\nTeam 2\n{nl+', '.join('<@!'+str(player)+'>' for player in team2)}",
                        color=discord.Color.green()
                    )
                    embed.set_footer(text="To mark the game as won, please use the /win command and attatch the screenshots of the rounds.")
                    msg = await txt.send(embed=embed)
                    await msg.pin()
                    for player in team1:
                        user = member.guild.get_member(player)
                        await user.move_to(vc2)
                    for player in team2:
                        user = member.guild.get_member(player)
                        await user.move_to(vc3)
                    
                    newOverWrites = {}
                    for player in team2:
                        newOverWrites[player] = discord.PermissionOverwrite(connect=False, speak=True)

                    newOverWritest2 = {}
                    for player in team1:
                        newOverWritest2[player] = discord.PermissionOverwrite(connect=False, speak=True)

                    await vc2.edit(overwrites=newOverWrites | vc2.overwrites)
                    await vc3.edit(overwrites=newOverWritest2 | vc3.overwrites)
                    await vc1.delete()

async def setup(bot: commands.Bot):
    await bot.add_cog(Autoqueue(bot))