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

# Start Flask in a separate daemon thread
threading.Thread(target=run_flask, daemon=True).start()

# --- Discord Bot Setup ---
FEED_SOURCES = [
    ('https://blog.humblebundle.com/rss/', 'Humble Bundle'),
    ('https://blog.fanatical.com/en/feed/', 'Fanatical'),
    ('https://gg.deals/rss/', 'GG.deals'),
    ('https://go-humble.com/feed/', 'Go-Humble')
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
    "Oooh, Anya thinks you might like this one!",
    "This bundle smells like peanuts and fun. 🥜",
    "Hehe~ Papa would buy this for sure.",
    "New games = more friends = world peace!",
    "Anya read minds and this one looked good!",
    "Waku waku~! Another bundle spotted!",
    "This one... has Anya vibes~",
    "Heh! Anya is best bundle spy!",
    "Spy report complete! Bundle delivered.",
    "Your mission is to click this bundle! 🕵️",
    "Loid-san would approve this deal!",
    "For the mission... for the fun... for the peanuts~",
    "Ooooooh! Shiny bundle!",
    "Hehe~ Anya pressed the button. Good button.",
    "Waku waku~! Anya did something useful!",
    "Hah! Anya's spy senses were tingling!",
    "Twilight would say this is 'efficient'!",
    "Bond says this bundle has good vibes.",
    "Yor would smash if no one buys this one!",
    "Anya detected value... 10/10 mission success!",
    "More games = less homework, right? 😈",
    "Waku waku~! Buy this or face peanut wrath!",
    "Shhh... secret bundle intel! 🤫",
    "Waku waku overload! This bundle is top tier~",
    "This deal made Anya's face go ⊙﹏⊙",
    "Loid doesn't know I posted this hehe~",
    "Why does bundle smell like... victory?",
    "Bundle detected! Waku waku alert~",
    "Hmm... yes. Very bundle. Very wow~",
    "This deal smells like spy success 🕶️",
    "No lie detector needed—this bundle is good!",
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
    "bundle hunting with psychic power",
    "dreaming of game world domination",
    "plotting secret bundle heist 👧",
    "sending Loid secret sales data",
    "writing fake homework while spying...",
    "Bond sees bundle future!",
    "Waku waku mode: ENGAGED!",
    "Analyzing bundle vibes~",
    "watching Yor train while updating feeds 🥵"
]

# --- Helper Functions ---

def is_bundle_post(title, link):
    keywords = ['bundle', 'sale', 'deal', 'game', 'offer', 'discount']
    title_lower = title.lower()
    if any(k in title_lower for k in keywords):
        return True
    link_lower = link.lower()
    if any(k in link_lower for k in keywords):
        return True
    return False

def fetch_thumbnail_from_url(url):
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image['content']
            img_src = soup.find('link', rel='image_src')
            if img_src and img_src.get('href'):
                return img_src['href']
    except Exception as e:
        print(f"Error fetching thumbnail from {url}: {e}")
    return None

# --- Commands ---

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Anya's brain ping is {latency}ms.")

@bot.command()
async def uptime(ctx):
    uptime_duration = datetime.now() - start_time
    await ctx.send(f"⏰ Anya has been spying for {str(uptime_duration).split('.')[0]}")

@bot.command()
async def status(ctx):
    await ctx.send("✅ Anya is online! Bundles are under watch.")

@bot.command()
async def info(ctx):
    embed = discord.Embed(title="🧠 Anya Info Report", color=discord.Color.pink())
    embed.add_field(name="Guilds", value=len(bot.guilds), inline=True)
    embed.add_field(name="Users", value=len(bot.users), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    commands_info = {
        "!ping": "Check Anya's latency",
        "!uptime": "See how long Anya has been working",
        "!info": "Spy report about the bot",
        "!status": "Current mission status",
        "!help": "What Anya can do",
        "!latestbundle": "Show latest detected game bundle"
    }
    embed = discord.Embed(title="📋 Spy Commands", color=discord.Color.gold())
    for cmd, desc in commands_info.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    embed.set_footer(text="Hehe~ Anya is a good bot.")
    await ctx.send(embed=embed)

@bot.command()
async def latestbundle(ctx):
    channel = ctx.channel
    for feed_url, source in FEED_SOURCES:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            continue
        # Find the first real bundle post
        for entry in feed.entries:
            if not is_bundle_post(entry.title, entry.link):
                continue
            embed = discord.Embed(
                title=f"🎮 Latest {source} Bundle!",
                description=entry.title,
                url=entry.link,
                color=discord.Color.orange() if "humble" in source.lower() else discord.Color.red(),
                timestamp=datetime.now()
            )
            if hasattr(entry, 'summary'):
                summary = entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary
                embed.add_field(name="📝 Summary", value=summary, inline=False)

            # Try to get image from feed first
            image_url = None
            if 'media_thumbnail' in entry:
                image_url = entry.media_thumbnail[0]['url']
            elif 'media_content' in entry:
                image_url = entry.media_content[0]['url']
            elif 'image' in entry:
                image_url = entry.image.href
            
            # If no image from feed, try to scrape from the page itself
            if not image_url:
                image_url = fetch_thumbnail_from_url(entry.link)
            
            if image_url:
                embed.set_image(url=image_url)

            embed.set_footer(text=random.choice(anya_quotes))
            await channel.send(embed=embed)
            break  # stop after first valid bundle found

# --- Background Task ---

@tasks.loop(minutes=10)
async def check_feeds():
    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Could not find channel with ID {channel_id}")
        return

    for feed_url, source in FEED_SOURCES:
        if feed_failures.get(feed_url, 0) >= MAX_FAILURES:
            print(f"Skipping {source} - too many failures.")
            continue

        try:
            response = requests.get(feed_url, timeout=10)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            feed = feedparser.parse(response.content)

            if not feed.entries:
                raise Exception("No entries in feed")

            for entry in feed.entries:
                if entry.title in posted_titles:
                    continue
                # Skip non-bundle posts
                if not is_bundle_post(entry.title, entry.link):
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
                    summary = entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary
                    embed.add_field(name="📝 Summary", value=summary, inline=False)

                # Try to get image from feed first
                image_url = None
                if 'media_thumbnail' in entry:
                    image_url = entry.media_thumbnail[0]['url']
                elif 'media_content' in entry:
                    image_url = entry.media_content[0]['url']
                elif 'image' in entry:
                    image_url = entry.image.href
                
                # If no image from feed, try to scrape from the page itself
                if not image_url:
                    image_url = fetch_thumbnail_from_url(entry.link)
                
                if image_url:
                    embed.set_image(url=image_url)

                embed.set_footer(text=random.choice(anya_quotes))
                await channel.send(embed=embed)

            feed_failures[feed_url] = 0  # reset failure count if successful

        except Exception as e:
            print(f"❌ Failed to fetch {source}: {e}")
            feed_failures[feed_url] = feed_failures.get(feed_url, 0) + 1

# --- On Ready Event ---

@bot.event
async def on_ready():
    print(f"✅ Anya has connected as {bot.user}")
    await bot.change_presence(activity=discord.Game(random.choice(anya_statuses)))
    check_feeds.start()

# --- Run Bot ---
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("ERROR: DISCORD_TOKEN environment variable is missing!")
else:
    bot.run(token)
