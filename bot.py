import os
import asyncio
import discord
from discord.ext import tasks
from mcstatus import JavaServer

# =========================================================
# CONFIGURATION
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

MINECRAFT_SERVER = "s1.anuverse.fun:25650"
STATUS_CHANNEL_ID = 1543874103449092217

MAX_PLAYERS = 20
UPDATE_INTERVAL = 30

# =========================================================
# DISCORD CLIENT
# =========================================================

intents = discord.Intents.default()

client = discord.Client(intents=intents)


# =========================================================
# MINECRAFT SERVER STATUS
# =========================================================

async def get_minecraft_status():

    def check_server():

        server = JavaServer.lookup(MINECRAFT_SERVER)

        status = server.status()

        players = []

        # Try Query first to get the complete player list
        try:

            query = server.query()

            players = query.players.list

        except Exception:

            # Fallback to the player sample
            if status.players.sample:

                players = [
                    player.name
                    for player in status.players.sample
                    if player.name
                ]

        return {
            "online": True,
            "players": status.players.online,
            "max": MAX_PLAYERS,
            "names": players,
            "ping": round(status.latency),
            "version": status.version.name,
            "motd": status.description
        }

    try:

        return await asyncio.to_thread(check_server)

    except Exception as error:

        print(f"Minecraft server error: {error}")

        return {
            "online": False,
            "players": 0,
            "max": MAX_PLAYERS,
            "names": [],
            "ping": 0,
            "version": "Unknown",
            "motd": "Server unavailable"
        }


# =========================================================
# PLAYER CAPACITY BAR
# =========================================================

def player_bar(players, maximum):

    if maximum <= 0:
        return "□□□□□□□□□□"

    percentage = players / maximum

    filled = round(percentage * 10)

    filled = max(0, min(10, filled))

    return "■" * filled + "□" * (10 - filled)


# =========================================================
# CLEAN MOTD
# =========================================================

def clean_motd(motd):

    if isinstance(motd, str):

        return motd.replace("\n", " ").strip()

    # Some Minecraft versions return MOTD as a dictionary
    if isinstance(motd, dict):

        try:

            return motd.get("text", "Kyronix Minecraft Server")

        except Exception:

            return "Kyronix Minecraft Server"

    return "Kyronix Minecraft Server"


# =========================================================
# UPDATE DISCORD STATUS
# =========================================================

@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_status():

    try:

        # Get Discord channel
        channel = await client.fetch_channel(
            STATUS_CHANNEL_ID
        )

        # Get Minecraft information
        data = await get_minecraft_status()

        # =================================================
        # SERVER OFFLINE
        # =================================================

        if not data["online"]:

            embed = discord.Embed(

                title="⚔️  KYRONIX",

                description=(
                    "### 🔴 Server Offline\n"
                    "The Minecraft server is currently unavailable."
                ),

                color=discord.Color.from_rgb(
                    220,
                    53,
                    69
                )
            )

            embed.add_field(

                name="🌐 Server",

                value="`s1.anuverse.fun:25650`",

                inline=False
            )

            embed.add_field(

                name="👥 Players",

                value="**0/20**",

                inline=True
            )

            embed.add_field(

                name="📡 Status",

                value="🔴 `Offline`",

                inline=True
            )

            embed.add_field(

                name="🔄 Next Restart",

                value="Every day at **6:00 AM GMT+6**",

                inline=False
            )

        # =================================================
        # SERVER ONLINE
        # =================================================

        else:

            players = data["players"]

            maximum = data["max"]

            ping = data["ping"]

            names = data["names"]

            version = data["version"]

            motd = clean_motd(data["motd"])

            # ---------------------------------------------
            # Capacity bar
            # ---------------------------------------------

            bar = player_bar(
                players,
                maximum
            )

            # ---------------------------------------------
            # Ping quality
            # ---------------------------------------------

            if ping < 80:

                ping_status = "🟢 Excellent"

            elif ping < 150:

                ping_status = "🟡 Good"

            elif ping < 250:

                ping_status = "🟠 High"

            else:

                ping_status = "🔴 Very High"

            # ---------------------------------------------
            # Player list
            # ---------------------------------------------

            if names:

                displayed_names = names[:20]

                player_list = "\n".join(

                    f"・`{name}`"

                    for name in displayed_names
                )

                if len(names) > 20:

                    player_list += (
                        f"\n・*and "
                        f"{len(names) - 20} more...*"
                    )

            else:

                player_list = "*No players online*"

            # ---------------------------------------------
            # ONLINE EMBED
            # ---------------------------------------------

            embed = discord.Embed(

                title="⚔️  KYRONIX",

                description=(
                    "### 🟢 Server Online\n"
                    "**Where legends are forged.**"
                ),

                color=discord.Color.from_rgb(
                    88,
                    166,
                    255
                )
            )

            # ---------------------------------------------
            # Players
            # ---------------------------------------------

            embed.add_field(

                name="👥 Players",

                value=(
                    f"**{players}/{maximum}**\n"
                    f"`{bar}`"
                ),

                inline=True
            )

            # ---------------------------------------------
            # Ping
            # ---------------------------------------------

            embed.add_field(

                name="📡 Ping",

                value=(
                    f"**{ping}ms**\n"
                    f"{ping_status}"
                ),

                inline=True
            )

            # ---------------------------------------------
            # Server Address
            # ---------------------------------------------

            embed.add_field(

                name="🌐 Server Address",

                value=(
                    "```"
                    "s1.anuverse.fun:25650"
                    "```"
                ),

                inline=False
            )

            # ---------------------------------------------
            # Online Players
            # ---------------------------------------------

            embed.add_field(

                name=f"👤 Online Players • {players}",

                value=player_list,

                inline=False
            )

            # ---------------------------------------------
            # Minecraft Version
            # ---------------------------------------------

            embed.add_field(

                name="🎮 Version",

                value=f"`{version}`",

                inline=True
            )

            # ---------------------------------------------
            # Restart
            # ---------------------------------------------

            embed.add_field(

                name="🔄 Next Restart",

                value="**Every day at 6:00 AM GMT+6**",

                inline=True
            )

            # ---------------------------------------------
            # MOTD
            # ---------------------------------------------

            embed.add_field(

                name="📝 Server MOTD",

                value=f"> {motd[:1024]}",

                inline=False
            )

        # =================================================
        # FOOTER
        # =================================================

        embed.set_footer(

            text="KYRONIX • Minecraft Community"
        )

        embed.timestamp = discord.utils.utcnow()

        # =================================================
        # FIND EXISTING BOT MESSAGE
        # =================================================

        async for message in channel.history(
            limit=20
        ):

            if message.author == client.user:

                await message.edit(
                    embed=embed
                )

                print(
                    "Status message updated."
                )

                return

        # =================================================
        # CREATE NEW MESSAGE
        # =================================================

        await channel.send(
            embed=embed
        )

        print(
            "Status message created."
        )

    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except discord.Forbidden:

        print(
            "ERROR: Missing Discord permissions."
        )

    except discord.NotFound:

        print(
            "ERROR: Status channel was not found."
        )

    except Exception as error:

        print(
            f"Status update error: {error}"
        )


# =========================================================
# BOT READY
# =========================================================

@client.event
async def on_ready():

    print(
        f"Logged in as {client.user}"
    )

    if not update_status.is_running():

        update_status.start()


# =========================================================
# START BOT
# =========================================================

if not DISCORD_TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

client.run(
    DISCORD_TOKEN
)
