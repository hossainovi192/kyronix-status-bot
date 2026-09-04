import os
import asyncio
import discord
from discord.ext import tasks
from mcstatus import JavaServer


# =========================================================
# CONFIGURATION
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Minecraft Server
MINECRAFT_SERVER = "s1.anuverse.fun:55556"

# Discord Status Channel
STATUS_CHANNEL_ID = 1543874103449092217

# Server Settings
MAX_PLAYERS = 20
UPDATE_INTERVAL = 30

# KYRONIX GIF
GIF_URL = (
    "https://media.discordapp.net/attachments/"
    "1543861808367009793/1543863839324635196/"
    "3dgifmaker14646.gif?"
    "ex=6a966abe&is=6a95193e&"
    "hm=911464c50ff13bade04e0a543500675ebae2ebdb6d01108a62160dab4e825a28&="
)


# =========================================================
# DISCORD CLIENT
# =========================================================

intents = discord.Intents.default()

# IMPORTANT:
# Required for the bot to read "-ip" messages
intents.message_content = True

client = discord.Client(intents=intents)


# =========================================================
# -IP COMMAND
# =========================================================

@client.event
async def on_message(message):

    # Ignore messages sent by the bot
    if message.author == client.user:
        return

    # Check for -ip command
    if message.content.strip().lower() == "-ip":

        embed = discord.Embed(

            title="⚒️ Server IP",

            description=(
                "**Where legends are forged.**"
            ),

            color=discord.Color.from_rgb(
                0,
                191,
                255
            )
        )

        # -------------------------------------------------
        # JAVA
        # -------------------------------------------------

        embed.add_field(

            name="Java :",

            value=(
                "```"
                "s1.anuverse.fun:55556"
                "```"
            ),

            inline=False
        )

        # -------------------------------------------------
        # BEDROCK
        # -------------------------------------------------

        embed.add_field(

            name="Bedrock:",

            value=(
                "```"
                "s1.anuverse.fun"
                "```"
            ),

            inline=False
        )

        # -------------------------------------------------
        # BEDROCK PORT
        # -------------------------------------------------

        embed.add_field(

            name="Port For Bedrock :",

            value=(
                "```"
                "55556"
                "```"
            ),

            inline=False
        )

        # -------------------------------------------------
        # GIF
        # -------------------------------------------------

        embed.set_image(
            url=GIF_URL
        )

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        embed.set_footer(

            text="🌐 KYRONIX • Minecraft Community"

        )

        # Send response
        await message.channel.send(
            embed=embed
        )


# =========================================================
# MINECRAFT SERVER STATUS
# =========================================================

async def get_minecraft_status():

    def check_server():

        server = JavaServer.lookup(
            MINECRAFT_SERVER
        )

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

            "version": status.version.name

        }

    try:

        return await asyncio.to_thread(
            check_server
        )

    except Exception as error:

        print(
            f"Minecraft server error: {error}"
        )

        return {

            "online": False,

            "players": 0,

            "max": MAX_PLAYERS,

            "names": [],

            "version": "Unknown"

        }


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

            names = data["names"]

            version = data["version"]


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

                value=f"**{players}/{maximum}**",

                inline=True

            )


            # ---------------------------------------------
            # Status
            # ---------------------------------------------

            embed.add_field(

                name="🟢 Status",

                value="`Online`",

                inline=True

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


        # =================================================
        # GIF
        # =================================================

        embed.set_image(

            url=GIF_URL

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
