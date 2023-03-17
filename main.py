import asyncio
import logging
import os
import traceback
import aiosqlite3
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.token: str = os.getenv("TOKEN")

        self.logger: logging.Logger = logging.getLogger("Bot")

        self.log: function = self.logger.info

        self.main_guild: int = int(os.getenv("MAIN_GUILD"))


    async def on_ready(self):
        self.log("Successfully connected to Discord")
        self.log("=======================================")
        self.log(f"Logged in as: {self.user}")
        self.log(f"User ID: {self.user.id}")
        self.log("=======================================")

        self.conn = await aiosqlite3.connect("db.db")


        await self.tree.sync(
            guild=discord.Object(id=bot.main_guild)
        )

    async def on_error(self, error: Exception):
        traceback.print_exc()

bot = Bot(
    command_prefix=os.getenv("PREFIX"),
    case_insensitive=True,
    intents=discord.Intents.all(),
    owner_ids=[int(os.getenv("OWNER_ID"))],
    status=discord.Status.idle,
    activity=discord.Game(name="scrims")
)

scrims = discord.app_commands.Group(
    name="scrims",
    description="...",
    guild_ids=[int(os.getenv("MAIN_GUILD"))]
)

async def load_cogs():
    for command in os.listdir("./cogs/hyperlands"):
        if command.endswith(".py"):
            try:
                bot.log("Attempting to load " + command)
                await bot.load_extension(f"cogs.hyperlands.{command[:-3]}")
                bot.log("Successfully loaded " + command)
            except:
                traceback.print_exc()
    return

async def start():
    discord.utils.setup_logging()
    await bot.start(bot.token)

async def main():
    await create_table()
    await bot.load_extension("jishaku")
    await load_cogs()
    await start()

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

    await cursor.execute(
        "CREATE TABLE IF NOT EXISTS tickets (channelId INTEGER, authorId INTEGER, claimedById INTEGER, messagesList TEXT, createdAt TEXT, closedAt TEXT, closedReason TEXT)"
    )

    await cursor.execute(
        "CREATE TABLE IF NOT EXISTS banned_words (word text)"
    )

    await cursor.execute('''CREATE TABLE IF NOT EXISTS moderation_logs (
        user_id INTEGER,
        moderator_id INTEGER,
        time INTEGER,
        type TEXT,
        reason TEXT,
        execution_time INTEGER,
        uuid TEXT
    )''')

    await cursor.execute('''CREATE TABLE IF NOT EXISTS mute_roles (
        user_id INTEGER,
        roles TEXT
    )''')


    await cursor.execute("SELECT * FROM count")
    await conn.commit()
    data = await cursor.fetchone()
    if not data:
        await cursor.execute("INSERT INTO count VALUES (?)", (0,))
        await conn.commit()
    await cursor.close()
    await conn.close()

asyncio.run(main())