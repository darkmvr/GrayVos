import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
import random
import requests
from datetime import datetime
from flask import Flask
import threading
from bs4 import BeautifulSoup

# --- Flask keep-alive server ---
app = Flask("")

@app.route("/")
def home():
    return random.choice([
        "Anya is alive and spying on bundles!",
        "Mission report: Anya still active.",
        "Bundle intel secure. Anya online! 🕵️‍♀️"
    ]), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# --- Discord Bot Setup ---
FEED_SOURCES = [
    ('https://blog.humblebundle.com/rss/', 'Humble Bundle'),
    ('https://blog.fanatical.com/en/feed/', 'Fanatical'),
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
posted_titles = set()
start_time = datetime.now()
channel_id = int(os.getenv('CHANNEL_ID'))

anya_quotes = [
    "Anya found this bundle! Waku waku~~! 🥜",
    "Anya spy mission: deliver new games. Success! 👀",
    "Hehe~ chichi would buy this for sure.",
    "New games = more friends = world peace!",
    "Waku waku~! Another bundle spotted!",
    "This one... has Anya vibes~",
    "Heh! Anya is best bundle spy!",
    "Your mission is to click this bundle! 🕵️",
    "Chichi would approve this deal!",
    "For the mission... for the fun... for the peanuts~",
    "Waku waku~! Buy this or face peanut wrath!",
    "Haha would smash if no one buys this one!",
    "Chichi says this deal is mission critical!",
    "Even Bond sees good vibes in this bundle~",
    "Loid doesn’t know I posted this hehe~",
    "Waku waku overload! This bundle is top tier~",
    "No lie detector needed—this bundle is good!"
]

@bot.command()
async def latestbundle(ctx):
    """Manually post the latest bundle from feeds"""
    channel = ctx.channel
    for feed_url, source in FEED_SOURCES:
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue

            for entry in feed.entries:
                if entry.title in posted_titles:
                    continue

                # Filter Humble: must have '/bundle/' in link
                if "humble" in source.lower():
                    if "/bundle/" not in entry.link:
                        continue

                # Filter Fanatical: must have '/bundle/' in entry link
                if "fanatical" in source.lower():
                    if "/bundle/" not in entry.link:
                        continue

                posted_titles.add(entry.title)
                embed = await create_bundle_embed(entry, source)
                await channel.send(embed=embed)
                return

            await ctx.send("Anya sees no new bundles right now~")
        except Exception as e:
            await ctx.send(f"Anya had a spy mission failure fetching the bundle: {e}")

async def create_bundle_embed(entry, source):
    embed = discord.Embed(
        title=f"🎮 New {source} Bundle!",
        description=entry.title,
        url=entry.link,
        color=discord.Color.orange() if "humble" in source.lower() else discord.Color.red(),
        timestamp=datetime.now()
    )

    summary = entry.summary if hasattr(entry, 'summary') else ""
    soup = BeautifulSoup(summary, "html.parser")
    text_summary = soup.get_text()[:200] + '...' if len(soup.get_text()) > 200 else soup.get_text()
    if text_summary.strip():
        embed.add_field(name="📝 Summary", value=text_summary, inline=False)

    thumb_url = None

    # Try media fields
    if 'media_thumbnail' in entry:
        thumb_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry:
        thumb_url = entry.media_content[0]['url']

    # Fallback: grab first image from summary HTML
    if not thumb_url:
        img = soup.find("img")
        if img and img.get("src"):
            thumb_url = img["src"]

    if thumb_url:
        embed.set_image(url=thumb_url)

    embed.set_footer(text=random.choice(anya_quotes))
    return embed

@tasks.loop(minutes=10)
async def check_feeds():
    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Could not find channel with ID {channel_id}")
        return

    for feed_url, source in FEED_SOURCES:
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue

            for entry in feed.entries:
                if entry.title in posted_titles:
                    continue

                # Filter Humble: only posts with '/bundle/' in link
                if "humble" in source.lower():
                    if "/bundle/" not in entry.link:
                        continue

                # Filter Fanatical: only posts with '/bundle/' in link
                if "fanatical" in source.lower():
                    if "/bundle/" not in entry.link:
                        continue

                posted_titles.add(entry.title)
                embed = await create_bundle_embed(entry, source)
                await channel.send(embed=embed)
                break

        except Exception as e:
            print(f"❌ Failed to fetch {source}: {e}")

@bot.event
async def on_ready():
    print(f"✅ Anya has connected as {bot.user}")
    await bot.change_presence(activity=discord.Game("spying on bundles 👀"))
    check_feeds.start()

token = os.getenv('DISCORD_TOKEN')
if not token:
    print("ERROR: DISCORD_TOKEN environment variable is missing!")
else:
    bot.run(token)
