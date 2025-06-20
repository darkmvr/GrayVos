import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
from datetime import datetime
from flask import Flask
import threading

# --- Flask keep-alive server ---
app = Flask("")

@app.route("/")
def home():
    return "I'm alive!", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Start Flask in a separate daemon thread (won't block program exit)
threading.Thread(target=run_flask, daemon=True).start()

# --- Discord Bot Setup ---
HUMBLE_RSS_URL = 'https://blog.humblebundle.com/rss/'
FANATICAL_RSS_URL = 'https://blog.fanatical.com/en/feed/'

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
posted_titles = set()
start_time = datetime.now()

try:
    channel_id = int(os.getenv('CHANNEL_ID'))
except (TypeError, ValueError):
    print("ERROR: CHANNEL_ID environment variable is not set or invalid!")
    channel_id = None

# --- Commands ---
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency is {latency}ms.")

@bot.command()
async def uptime(ctx):
    uptime_duration = datetime.now() - start_time
    await ctx.send(f"⏰ Uptime: {str(uptime_duration).split('.')[0]}")

@bot.command()
async def status(ctx):
    await ctx.send("✅ Bot is online and monitoring bundles.")

@bot.command()
async def info(ctx):
    embed = discord.Embed(title="🤖 Bot Info", color=discord.Color.blurple())
    embed.add_field(name="Guilds", value=len(bot.guilds), inline=True)
    embed.add_field(name="Users", value=len(bot.users), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    commands_info = {
        "!ping": "Check bot latency",
        "!uptime": "Show how long the bot has been online",
        "!info": "Display bot and system info",
        "!status": "Show bot monitoring status",
        "!help": "Show this help message"
    }
    embed = discord.Embed(title="📋 Commands", color=discord.Color.gold())
    for cmd, desc in commands_info.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    await ctx.send(embed=embed)

# --- Background Task ---
@tasks.loop(minutes=10)
async def check_feeds():
    if channel_id is None:
        print("Skipping feed check: invalid CHANNEL_ID")
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Could not find channel with ID {channel_id}")
        return

    feeds = [
        (HUMBLE_RSS_URL, "Humble Bundle"),
        (FANATICAL_RSS_URL, "Fanatical")
    ]

    for feed_url, source in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if entry.title not in posted_titles:
                posted_titles.add(entry.title)

                embed = discord.Embed(
                    title=f"🎮 New Bundle from {source}",
                    description=entry.title,
                    url=entry.link,
                    color=discord.Color.orange() if source == "Humble Bundle" else discord.Color.red()
                )

                if hasattr(entry, 'summary'):
                    summary = entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary
                    embed.add_field(name="Description", value=summary, inline=False)

                embed.set_footer(text=f"Posted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await channel.send(embed=embed)

# --- On Ready Event ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game("bundles | !help"))
    if not check_feeds.is_running():
        check_feeds.start()

# --- Run Bot ---
token = os.getenv('DISCORD_TOKEN')
if token is None:
    print("ERROR: DISCORD_TOKEN environment variable is not set!")
else:
    bot.run(token)
