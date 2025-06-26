import discord
from discord.ext import commands, tasks
import feedparser
from bs4 import BeautifulSoup
import asyncio
import os
from datetime import datetime
from flask import Flask
import threading
import random
import requests

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

# --- Bot setup ---
FEED_SOURCES = [
    ('https://blog.humblebundle.com/rss/', 'Humble Bundle'),
    ('https://blog.fanatical.com/en/feed/', 'Fanatical'),
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
posted_titles = set()
channel_id = int(os.getenv('CHANNEL_ID'))
start_time = datetime.now()

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

# Helper: Check if entry looks like a real bundle post
def is_valid_bundle(entry):
    title = entry.title.lower()
    # Must mention 'bundle' or 'software' or 'game'
    if not any(keyword in title for keyword in ['bundle', 'software', 'game']):
        return False
    # Exclude unwanted stuff
    exclude_keywords = [
        'price increase', 'celebrating', 'donation', 'partnership',
        'community', 'impact', 'support', 'news', 'update', 'announcement',
        'sale start', 'price change', 'price drop', 'price increase', 'coupon'
    ]
    if any(ex in title for ex in exclude_keywords):
        return False
    return True

# Extract direct bundle URL from entry summary or content
def extract_direct_bundle_url(entry, source):
    # Check if entry.link itself is a direct bundle URL (contains humblebundle.com/games or fanatical.com/en/bundle)
    if 'humblebundle.com/games' in entry.link or 'fanatical.com/en/bundle' in entry.link:
        return entry.link

    # Else try to parse HTML in summary/content and find first direct bundle URL
    content_html = ''
    if hasattr(entry, 'summary'):
        content_html = entry.summary
    elif hasattr(entry, 'content'):
        content_html = entry.content[0].value if len(entry.content) > 0 else ''

    soup = BeautifulSoup(content_html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Look for humble or fanatical direct bundle URLs
        if ('humblebundle.com/games' in href or 'fanatical.com/en/bundle' in href) and href.startswith('http'):
            # Clean URL from tracking params if needed
            href_clean = href.split('?')[0]
            return href_clean
    return None

def get_thumbnail(entry):
    # Extract from <media:thumbnail> or content
    if 'media_thumbnail' in entry:
        return entry.media_thumbnail[0]['url']
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    # Fallback: parse HTML for img tags
    content_html = ''
    if hasattr(entry, 'summary'):
        content_html = entry.summary
    elif hasattr(entry, 'content'):
        content_html = entry.content[0].value if len(entry.content) > 0 else ''

    soup = BeautifulSoup(content_html, 'html.parser')
    img = soup.find('img')
    return img['src'] if img else None

@bot.event
async def on_ready():
    print(f"✅ Anya connected as {bot.user}")
    await bot.change_presence(activity=discord.Game(random.choice(anya_statuses)))
    check_feeds.start()

@tasks.loop(minutes=10)
async def check_feeds():
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"❌ Missing channel: {channel_id}")
        return

    for feed_url, source in FEED_SOURCES:
        try:
            response = requests.get(feed_url, timeout=10)
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                if entry.title in posted_titles:
                    continue
                if not is_valid_bundle(entry):
                    continue
                direct_url = extract_direct_bundle_url(entry, source)
                if not direct_url:
                    # Skip if no direct bundle URL found
                    continue

                posted_titles.add(entry.title)

                embed = discord.Embed(
                    title=f"🎮 {entry.title}",
                    url=direct_url,
                    color=discord.Color.orange() if 'humble' in source.lower() else discord.Color.red(),
                    timestamp=datetime.now()
                )
                summary = BeautifulSoup(entry.summary, 'html.parser').get_text() if hasattr(entry, 'summary') else ''
                embed.add_field(name="📝 Summary", value=summary[:200] + '...' if len(summary) > 200 else summary, inline=False)

                thumb = get_thumbnail(entry)
                if thumb:
                    embed.set_image(url=thumb)

                embed.set_footer(text=random.choice(anya_quotes))
                await channel.send(embed=embed)
                break  # Only post one new bundle per feed check
        except Exception as e:
            print(f"❌ Error fetching or parsing feed '{source}': {e}")

# --- Commands ---
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Anya brain ping: {round(bot.latency * 1000)}ms")

@bot.command()
async def uptime(ctx):
    up = str(datetime.now() - start_time).split('.')[0]
    await ctx.send(f"⏰ Anya spying since: {up}")

@bot.command()
async def latestbundle(ctx):
    for feed_url, source in FEED_SOURCES:
        try:
            response = requests.get(feed_url, timeout=10)
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                if not is_valid_bundle(entry):
                    continue
                direct_url = extract_direct_bundle_url(entry, source)
                if not direct_url:
                    continue

                embed = discord.Embed(
                    title=f"🎮 {entry.title}",
                    url=direct_url,
                    color=discord.Color.orange() if 'humble' in source.lower() else discord.Color.red(),
                    timestamp=datetime.now()
                )
                summary = BeautifulSoup(entry.summary, 'html.parser').get_text() if hasattr(entry, 'summary') else ''
                embed.add_field(name="📝 Summary", value=summary[:200] + '...' if len(summary) > 200 else summary, inline=False)

                thumb = get_thumbnail(entry)
                if thumb:
                    embed.set_image(url=thumb)

                embed.set_footer(text=random.choice(anya_quotes))
                await ctx.send(embed=embed)
                return
            await ctx.send("Anya sees no new bundles right now~")
        except Exception as e:
            await ctx.send(f"Anya had a spy mission failure fetching the bundle: {e}")

@bot.command()
async def status(ctx):
    await ctx.send("✅ Anya is online and watching bundles!")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📋 Anya's Spy Commands", color=discord.Color.pink())
    embed.add_field(name="!ping", value="Anya's brain ping", inline=False)
    embed.add_field(name="!uptime", value="How long Anya has worked", inline=False)
    embed.add_field(name="!latestbundle", value="Get latest bundle manually", inline=False)
    embed.add_field(name="!status", value="Check Anya's status", inline=False)
    embed.set_footer(text="Anya is a good bot. Waku waku~")
    await ctx.send(embed=embed)

# --- Run Bot ---
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ DISCORD_TOKEN not found in environment.")
