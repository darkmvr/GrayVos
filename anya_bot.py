import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
from datetime import datetime

# Feeds
HUMBLE_RSS_URL = 'https://blog.humblebundle.com/rss/'
FANATICAL_RSS_URL = 'https://blog.fanatical.com/en/feed/'

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
posted_titles = set()
start_time = datetime.now()
channel_id = int(os.getenv('CHANNEL_ID', '1384937321555689642'))

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
    channel = bot.get_channel(channel_id)
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

# --- Ready Event ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(
        activity=discord.Game("bundles | !help")
    )
    check_feeds.start()

# --- Run ---
bot.run(os.getenv('DISCORD_TOKEN'))
