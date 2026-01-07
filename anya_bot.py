import discord
from discord.ext import commands
import os
import random
import threading
from flask import Flask
import yt_dlp

# --- Flask keep-alive ---
app = Flask("")

@app.route("/")
def home():
    return random.choice([
        "Anya is alive and listening!",
        "Mission report: Anya online.",
        "Waku waku~! Anya is ready!",
    ]), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# --- Discord bot ---
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

# --- Voice/music commands ---
@bot.command(name="anya")
async def anya_voice(ctx, mode: str = None, *, query: str = None):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Join a voice channel first! 😤")
        return

    voice_channel = ctx.author.voice.channel

    # Show help
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

        if ctx.voice_client is None:
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "default_search": "ytsearch",
            "noplaylist": True,
            # Uncomment if using cookies
            # "cookiefile": "cookies.txt"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            url = info["url"]
            title = info.get("title", "Unknown")

        vc.play(
            discord.FFmpegPCMAudio(url),
            after=lambda e: print(f"Audio ended: {e}")
        )

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

# --- Join/Leave commands ---
@bot.command(name="anyajoin")
async def anya_join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You need to be in a voice channel! 😤")
        return
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(voice_channel)
        await ctx.send(f"Anya moves to {voice_channel.name} 🕵️‍♀️")
    else:
        await voice_channel.connect()
        await ctx.send(f"Anya joins {voice_channel.name}! 🎶")

@bot.command(name="anyaleave")
async def anya_leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Anya leaves the voice channel. Bye bye~ 👋")
    else:
        await ctx.send("Anya isn't in any voice channel right now~ 😢")

# --- Run bot ---
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("Missing DISCORD_TOKEN!")
