import os
import asyncio
import discord
from discord.ext import tasks
from mcstatus import JavaServer

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

MINECRAFT_SERVER = "s1.anuverse.fun:25650"
STATUS_CHANNEL_ID = 1543874103449092217

UPDATE_INTERVAL = 30

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def get_minecraft_status():

    def check_server():
        server = JavaServer.lookup(MINECRAFT_SERVER)
        status = server.status()

        players = []

        try:
            query = server.query()
            players = query.players.list
        except Exception:
            if status.players.sample:
                players = [
                    player.name
                    for player in status.players.sample
                ]

        return {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "names": players,
            "ping": round(status.latency)
        }

    try:
        return await asyncio.to_thread(check_server)

    except Exception as error:
        print(f"Minecraft server error: {error}")

        return {
            "online": False,
            "players": 0,
            "max": 50,
            "names": [],
            "ping": 0
        }


@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_status():

    channel = client.get_channel(STATUS_CHANNEL_ID)

    if channel is None:
        print("ERROR: Discord channel not found.")
        return

    data = await get_minecraft_status()

    if not data["online"]:

        embed = discord.Embed(
            title="⚔ KYRONIX STATUS",
            description="🔴 **Server Offline**",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🌐 Server",
            value="`s1.anuverse.fun:25650`",
            inline=False
        )

    else:

        names = data["names"]

        if names:
            player_list = "\n".join(
                f"🟢 {name}" for name in names
            )
        else:
            player_list = "No players online."

        embed = discord.Embed(
            title="⚔ KYRONIX STATUS",
            description="🟢 **Server Online**",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="👥 Players",
            value=f"`{data['players']}/{data['max']}`",
            inline=True
        )

        embed.add_field(
            name="📡 Ping",
            value=f"`{data['ping']}ms`",
            inline=True
        )

        embed.add_field(
            name="👤 Online Players",
            value=player_list[:1024],
            inline=False
        )

        embed.add_field(
            name="🌐 Server",
            value="`s1.anuverse.fun:25650`",
            inline=False
        )

    embed.set_footer(
        text="Kyronix • Updates every 30 seconds"
    )

    async for message in channel.history(limit=20):

        if message.author == client.user:
            await message.edit(embed=embed)
            return

    await channel.send(embed=embed)


@client.event
async def on_ready():

    print(f"Logged in as {client.user}")

    if not update_status.is_running():
        update_status.start()


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is missing.")

client.run(DISCORD_TOKEN)
