import discord
from discord.ext import commands, tasks
import feedparser
import requests
import os
import random
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask
import threading

# --- Flask keep-alive ---
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

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()

# --- Discord bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

FEED_SOURCES = [
    ('https://blog.humblebundle.com/rss/', 'Humble Bundle'),
    ('https://blog.fanatical.com/en/feed/', 'Fanatical'),
    ('https://gg.deals/news/feed/?store=20,40&type=1', 'GG.deals')
]

posted_titles = set()
channel_id = int(os.getenv('CHANNEL_ID'))

# your anya_quotes unchanged...
anya_quotes = [ ... ]  # keep all your quotes

@bot.event
async def on_ready():
    print(f"✅ Anya has connected as {bot.user}")
    check_feeds.start()

@bot.command()
async def latestbundle(ctx):
    await process_feeds(ctx.send)

def looks_like_bundle(entry):
    title = entry.title.lower()
    return any(k in title for k in ["bundle", "choice", "software", "platinum", "mystery", "build your own"])

def build_bundle_embed(entry, source):
    embed = discord.Embed(
        title=f"🎮 New {source} Bundle!",
        description=entry.title,
        url=entry.link,
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    summary = BeautifulSoup(getattr(entry, 'summary', ''), 'html.parser').get_text()
    if summary:
        embed.add_field(name="📝 Summary", value=(summary[:200] + "...") if len(summary) > 200 else summary, inline=False)
    try:
        resp = requests.get(entry.link, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        img = soup.find("meta", property="og:image")
        if img and img.get("content"):
            embed.set_image(url=img["content"])
    except Exception:
        pass
    embed.set_footer(text=random.choice(anya_quotes))
    return embed

async def process_feeds(send_func):
    for url, source in FEED_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.title in posted_titles:
                continue
            if not looks_like_bundle(entry):
                continue
            posted_titles.add(entry.title)
            await send_func(embed=build_bundle_embed(entry, source))
            return
    await send_func("Anya sees no new bundles right now~")

@tasks.loop(minutes=10)
async def check_feeds():
    channel = bot.get_channel(channel_id)
    if channel:
        await process_feeds(channel.send)
    else:
        print("Channel not found")

# Run
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Missing DISCORD_TOKEN!")
else:
    bot.run(token)
