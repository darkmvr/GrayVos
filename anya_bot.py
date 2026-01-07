import discord
from discord.ext import commands
import os
import random
import yt_dlp
import asyncio
from discord import FFmpegPCMAudio

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

anya_music_quotes = [
    "Waku waku~! Music makes Anya brain go brrr~ 🎶",
    "Anya likes this song! Peanut rhythm detected! 🥜",
    "This song is VERY spy approved 🕵️‍♀️🎧",
    "Music makes mission easier! Probably!",
]

# --- Events ---
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("spying on music 👀"))
    print(f"✅ Anya has connected as {bot.user}")

# --- Main command ---
@bot.command(name="anya")
async def anya_voice(ctx, mode: str = None, *, query: str = None):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Join a voice channel first! 😤")
        return

    voice_channel = ctx.author.voice.channel

    # Help command
    if mode is None:
        await ctx.send(
            "**Anya voice commands:**\n"
            "`!anya watch` → YouTube Watch Together 📺\n"
            "`!anya play <song>` → play music 🎵\n"
            "`!anya stop` → stop music ⛔"
        )
        return

    # Watch Together
    if mode.lower() == "watch":
        invite = await voice_channel.create_invite(
            target_application_id=880218394199220334,
            target_type=2,
            max_age=0
        )
        await ctx.send(f"📺 **Anya starts YouTube time!**\n👉 {invite.url}")
        return

    # Play music
    if mode.lower() == "play":
        if not query:
            await ctx.send("Anya needs a song to play! 😠")
            return

        vc = ctx.voice_client
        if vc is None:
            vc = await voice_channel.connect()

        # Use yt-dlp to get direct audio stream
        ydl_opts = {"format": "bestaudio/best", "quiet": True, "default_search": "ytsearch", "noplaylist": True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                title = info.get("title", "Unknown")
                url = info["url"]
        except Exception as e:
            await ctx.send(f"❌ Failed to get the song: {e}")
            return

        if vc.is_playing():
            vc.stop()

        # --- DEPLOY-SAFE STREAMING ---
        # FFmpeg reads from stdin instead of passing URL as argument
        ffmpeg_command = [
            "ffmpeg",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-i", url,
            "-vn",
            "-f", "s16le",
            "pipe:1"
        ]
        audio_source = FFmpegPCMAudio(executable="ffmpeg", source=url, pipe=True, options="-vn", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        vc.play(audio_source, after=lambda e: print(f"Audio ended: {e}"))

        await ctx.send(f"🎶 **Anya plays:** {title} ♪\n{random.choice(anya_music_quotes)}")
        return

    # Stop music
    if mode.lower() == "stop":
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Music stopped! Back to spy work 😌")
        else:
            await ctx.send("Anya wasn't playing anything~")
        return

    await ctx.send(f"Unknown mode `{mode}`. Type `!anya` for commands.")

# --- Join / Leave commands ---
@bot.command(name="anyajoin")
async def anya_join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You need to be in a voice channel! 😤")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
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

# --- Run bot ---
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is missing!")

bot.run(token)
