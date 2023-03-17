import aiosqlite3
from typing import List
import traceback
import discord

async def create_table():
    conn = await aiosqlite3.connect("db.db")
    cursor = await conn.cursor()
    await cursor.execute(
        "CREATE TABLE IF NOT EXISTS hyperlands (p1 INTEGER, p2 INTEGER, p3 INTEGER, p4 INTEGER, p5 INTEGER, p6 INTEGER, p7 INTEGER, p8 INTEGER, t1 TEXt, t2 TEXT, t1c INTEGER, t2c INTEGER, status TEXT, channel_id INTEGER, vc1 INTEGER, vc2 INTEGER, vc3 INTEGER, current_time TEXT, winner INTEGER, end_time TEXT)"
    )
    await cursor.execute(
        "CREATE TABLE IF NOT EXISTS playersElo (id INTEGER, name STRING, elo INTEGER, games INTEGER, wins INTEGER, losses INTEGER, current_ws INTEGER)"
    )
    await cursor.execute(
        "CREATE TABLE IF NOT EXISTS count (num INTEGER)"
    )
    await cursor.execute("SELECT * FROM count")
    await conn.commit()
    data = await cursor.fetchone()
    if not data:
        await cursor.execute("INSERT INTO count VALUES (?)", (0,))
        await conn.commit()
    await cursor.close()
    await conn.close()

EloDict = {
    range(0, 200): {"gains": 35, "loses": 10, "name": "Beginner"},
    range(200, 400): {"gains": 30, "loses": 15, "name": "Median"},
    range(400, 600): {"gains": 25, "loses": 20, "name": "Proficient"},
    range(600, 800): {"gains": 20, "loses": 25, "name": "Advanced"},
    range(800, 1000): {"gains": 15, "loses": 30, "name": "Master"},
    range(1400, 1800): {"gains": 10, "loses": 35, "name": "Grandmaster"},
    1200: {"gains": 5, "loses": 40, "name": "Infinity"},
}

def give_elo(currentElo: int):
    if currentElo >= 2200:
        return 10, 25
    for key in EloDict:
        if currentElo in key:
            return EloDict[key]["gains"], EloDict[key]["loses"]

def cooldown(interaction: discord.Interaction):
    # roles = [1068941099613307040, 1074054543572217986, 1068796827706609674, 1079548620728184912, 1073447223263776789, 1069322745139171358, 1068794634073022475, 1082398067216613386, 1073859809922793503, 1073404341555314728]
    # roles = [interaction.guild.get_role(role) for role in roles]

    # if any(role in interaction.author.roles for role in roles):
    #     return None
    return discord.app_commands.Cooldown(1, float(60*60*25))

async def set_win(players: List[discord.Member]):
    conn = await aiosqlite3.connect("db.db")
    cursor = await conn.cursor()
    for member in players:
        await cursor.execute("SELECT * FROM playersElo WHERE id = ?", (member.id,))
        data = await cursor.fetchone()
        if not data:
            gains, loses = give_elo(0)
            newElo = 0 + gains
            await cursor.execute("INSERT INTO playersElo VALUES (?, ?, ?, ?, ?, ?, ?)", (member.id, member.name, newElo, 1, 1, 0, 0))
            await conn.commit()
            try:
                await member.edit(nick=f"{newElo} | {member.name}")
            except Exception as e:
                traceback.print_exc()
        else:
            gains, loses = give_elo(data[2])
            newElo = data[2] + gains
            await cursor.execute("UPDATE playersElo SET elo = ?, wins = ?, games = ? WHERE id = ?", (newElo, data[4] + 1, data[3] + 1, member.id))
            await conn.commit()
            try:
                await member.edit(nick=f"{newElo} | {member.name}")
            except Exception as e:
                traceback.print_exc()

async def close_game(txt: discord.TextChannel, vc1: discord.VoiceChannel, vc2: discord.VoiceChannel):
    await txt.delete()
    await vc1.delete()
    await vc2.delete()

async def set_loss(players: List[discord.Member]):
    conn = await aiosqlite3.connect("db.db")
    cursor = await conn.cursor()
    for member in players:
        await cursor.execute("SELECT * FROM playersElo WHERE id = ?", (member.id,))
        data = await cursor.fetchone()
        if not data:
            gains, loses = give_elo(0)
            newElo = 0
            await cursor.execute("INSERT INTO playersElo VALUES (?, ?, ?, ?, ?, ?, ?)", (member.id, member.name, newElo, 1, 0, 1, 0))
            await conn.commit()
            try:
                await member.edit(nick=f"{newElo} | {data[1]}")
            except Exception as e:
                traceback.print_exc()
        else:
            gains, loses = give_elo(data[2])
            newElo = data[2] - loses
            if newElo < 0:
                newElo = 0
            await cursor.execute("UPDATE playersElo SET elo = ?, losses = ?, games = ? WHERE id = ?", (newElo, data[5] + 1, data[3] + 1, member.id))
            await conn.commit()
            try:
                await member.edit(nick=f"{newElo} | {member.name}")
            except Exception as e:
                traceback.print_exc()

async def setup(bot):
    pass
