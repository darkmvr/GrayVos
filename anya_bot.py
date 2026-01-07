import discord
from discord.ext import commands
import os
import random
import yt_dlp
import asyncio
from discord import FFmpegPCMAudio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

anya_music_quotes = [
    "Waku waku~! Music makes Anya brain go brrr~ 🎶",
    "Anya likes this song! Peanut rhythm detected! 🥜",
    "This song is VERY spy approved 🕵️‍♀️🎧",
    "Music makes mission easier! Probably!",
]

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("spying on music 👀"))
    print(f"✅ Anya has connected as {bot.user}")

async def stream_youtube_audio(vc, query):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "default_search": "ytsearch",
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        title = info.get("title", "Unknown")
        url = info["url"]

    # Run ffmpeg as subprocess directly (no Bash, no long URLs)
    ffmpeg_cmd = [
        "ffmpeg",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-i", url,
        "-f", "s16le",
        "-ar", "48000",
        "-ac", "2",
        "pipe:1"
    ]

    # Start the subprocess
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    # Create a Discord audio source from the subprocess stdout
    source = FFmpegPCMAudio(process.stdout)
    vc.play(source, after=lambda e: print(f"Audio ended: {e}"))
    return title

@bot.command(name="anya")
async def anya_voice(ctx, mode: str = None, *, query: str = None):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Join a voice channel first! 😤")
        return

    voice_channel = ctx.author.voice.channel
    vc = ctx.voice_client or await voice_channel.connect()

    if mode is None:
        await ctx.send(
            "**Anya voice commands:**\n"
            "`!anya watch` → YouTube Watch Together 📺\n"
            "`!anya play <song>` → play music 🎵\n"
            "`!anya stop` → stop music ⛔"
        )
        return

    if mode.lower() == "watch":
        invite = await voice_channel.create_invite(
            target_application_id=880218394199220334,
            target_type=2,
            max_age=0
        )
        await ctx.send(f"📺 **Anya starts YouTube time!**\n👉 {invite.url}")
        return

    if mode.lower() == "play":
        if not query:
            await ctx.send("Anya needs a song to play! 😠")
            return

        if vc.is_playing():
            vc.stop()

        title = await stream_youtube_audio(vc, query)
        await ctx.send(f"🎶 **Anya plays:** {title} ♪\n{random.choice(anya_music_quotes)}")
        return

    if mode.lower() == "stop":
        if vc:
            await vc.disconnect()
            await ctx.send("🛑 Music stopped! Back to spy work 😌")
        else:
            await ctx.send("Anya wasn't playing anything~")
        return

    await ctx.send(f"Unknown mode `{mode}`. Type `!anya` for commands.")

@bot.command(name="anyajoin")
async def anya_join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You need to be in a voice channel! 😤")
        return
    channel = ctx.author.voice.channel
    vc = ctx.voice_client
    if vc:
        await vc.move_to(channel)
        await ctx.send(f"Anya moves to {channel.name} 🕵️‍♀️")
    else:
        await channel.connect()
        await ctx.send(f"Anya joins {channel.name}! 🎶")

@bot.command(name="anyaleave")
async def anya_leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Anya leaves the voice channel. Bye bye~ 👋")
    else:
        await ctx.send("Anya isn't in any voice channel right now~ 😢")

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is missing!")

bot.run(token)
