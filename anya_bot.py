import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
from datetime import datetime
from flask import Flask
import threading
import random
import requests
from bs4 import BeautifulSoup

# --- Flask keep-alive server ---
app = Flask("")

@app.route("/")
def home():
    return random.choice([
        "Anya is alive and spying on bundles!",
        "Mission report: Anya still active.",
        "Bundle intel secure. Anya online!",
        "Waku waku~! Anya is watching RSS feeds!",
        "Anya is doing important spy work rn~ 🕵️‍♀️"
    ]), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# --- Discord Bot Setup ---
FEED_SOURCES = [
    ('https://blog.humblebundle.com/rss/', 'Humble Bundle'),
    ('https://blog.fanatical.com/en/feed/', 'Fanatical')
]

feed_failures = {}
MAX_FAILURES = 3

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
posted_titles = set()
start_time = datetime.now()

channel_id = int(os.getenv('CHANNEL_ID'))

# --- Anya Personality Snippets ---
anya_quotes = [
    "Anya found this bundle! Waku waku~~! 🥜",
    "Anya spy mission: deliver new games. Success! 👀",
    "Oooh, Anya thinks chichi would like this one!",
    "This bundle smells like peanuts and fun. 🥜",
    "Hehe~ haha would smash if no one buys this one!",
    "New games = more friends = world peace!",
    "Anya read minds and this one looked good!",
    "Waku waku~! Another bundle spotted!",
    "This one... has Anya vibes~",
    "Heh! Anya is best bundle spy!",
    "Spy report complete! Bundle delivered.",
    "Your mission is to click this bundle! 🕵️",
    "Chichi would approve this deal!",
    "For the mission... for the fun... for the peanuts~",
    "Ooooooh! Shiny bundle!",
    "Hehe~ Anya pressed the button. Good button.",
    "Waku waku~! Anya did something useful!",
    "Twilight would say this is 'efficient'!",
    "Bond says this bundle has good vibes.",
    "Anya detected value... 10/10 mission success!",
    "More games = less homework, right? 😈",
    "Waku waku~! Buy this or face peanut wrath!",
    "Shhh... secret bundle intel! 🤫",
    "This deal made Anya's face go ⊙＿⊙",
    "Why does bundle smell like... victory?",
    "Hmm... yes. Very bundle. Very wow~",
    "This deal smells like spy success 🕶️",
    "Even Chimera-san approves this one~"
]

anya_statuses = [
    "spying on game bundles 👀",
    "thinking about peanuts and bundles 🥜",
    "reporting bundle findings for world peace",
    "waiting for new missions...",
    "observing humans buy bundles",
    "gathering bundle intel 🧠",
    "tracking shiny discounts 💰",
    "on peanut break (still watching) 🥜",
    "dreaming of game world domination",
    "plotting secret bundle heist 👧",
    "sending chichi secret sales data",
    "writing fake homework while spying...",
    "Bond sees bundle future!",
    "Waku waku mode: ENGAGED!",
    "Analyzing bundle vibes~"
]

# --- Helper ---
def is_bundle_post(entry):
    title = entry.title.lower()
    return any(keyword in title for keyword in ["bundle", "choice", "deal", "reveal", "collection"])

# --- Commands ---
@bot.command()
async def latestbundle(ctx):
    for feed_url, source in FEED_SOURCES:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            continue
        for entry in feed.entries:
            if not is_bundle_post(entry):
                continue
            embed = discord.Embed(
                title=f"🎮 Latest {source} Bundle!",
                description=entry.title,
                url=entry.link,
                color=discord.Color.orange() if "humble" in source.lower() else discord.Color.red(),
                timestamp=datetime.now()
            )
            if hasattr(entry, 'summary'):
                soup = BeautifulSoup(entry.summary, 'html.parser')
                text_summary = soup.get_text()
                summary = text_summary[:200] + '...' if len(text_summary) > 200 else text_summary
                embed.add_field(name="📜 Summary", value=summary, inline=False)

            if hasattr(entry, 'media_thumbnail'):
                embed.set_image(url=entry.media_thumbnail[0]['url'])
            elif hasattr(entry, 'media_content'):
                embed.set_image(url=entry.media_content[0]['url'])

            embed.set_footer(text=random.choice(anya_quotes))
            await ctx.send(embed=embed)
            return  # only post one
    await ctx.send("No new bundles found waku waku~")

# --- Feed Checker ---
@tasks.loop(minutes=10)
async def check_feeds():
    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Could not find channel with ID {channel_id}")
        return

    for feed_url, source in FEED_SOURCES:
        if feed_failures.get(feed_url, 0) >= MAX_FAILURES:
            continue

        try:
            response = requests.get(feed_url, timeout=10)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            feed = feedparser.parse(response.content)
            if not feed.entries:
                raise Exception("No entries in feed")

            for entry in feed.entries:
                if entry.title in posted_titles or not is_bundle_post(entry):
                    continue

                posted_titles.add(entry.title)

                embed = discord.Embed(
                    title=f"🎮 New {source} Bundle!",
                    description=entry.title,
                    url=entry.link,
                    color=discord.Color.orange() if "humble" in source.lower() else discord.Color.red(),
                    timestamp=datetime.now()
                )

                if hasattr(entry, 'summary'):
                    soup = BeautifulSoup(entry.summary, 'html.parser')
                    text_summary = soup.get_text()
                    summary = text_summary[:200] + '...' if len(text_summary) > 200 else text_summary
                    embed.add_field(name="📜 Summary", value=summary, inline=False)

                if hasattr(entry, 'media_thumbnail'):
                    embed.set_image(url=entry.media_thumbnail[0]['url'])
                elif hasattr(entry, 'media_content'):
                    embed.set_image(url=entry.media_content[0]['url'])

                embed.set_footer(text=random.choice(anya_quotes))
                await channel.send(embed=embed)

            feed_failures[feed_url] = 0

        except Exception as e:
            print(f"❌ Failed to fetch {source}: {e}")
            feed_failures[feed_url] = feed_failures.get(feed_url, 0) + 1

# --- On Ready ---
@bot.event
async def on_ready():
    print(f"✅ Anya is online as {bot.user}")
    await bot.change_presence(activity=discord.Game(random.choice(anya_statuses)))
    check_feeds.start()

# --- Run Bot ---
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("ERROR: DISCORD_TOKEN environment variable is missing!")
