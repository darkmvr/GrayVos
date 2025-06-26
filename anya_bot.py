import discord
from discord.ext import commands, tasks
import feedparser
from bs4 import BeautifulSoup
import requests
import asyncio
import os
from datetime import datetime
from flask import Flask
import threading
import random

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
    "Anya spy mission: deliver new games. Success! 😍",
    "Hehe~ ちち would buy this for sure.",
    "Yor would smash if no one buys this one!",
    "Anya read minds and this one looked good!",
    "Loid-san would approve this deal!",
    "For the mission... for the fun... for the peanuts~",
    "Loid doesn't know I posted this hehe~",
    "Waku waku~! Buy this or face peanut wrath!",
    "Even Chimera-san approves this one~"
]

anya_statuses = [
    "spying on game bundles 👀",
    "thinking about peanuts and bundles 🥜",
    "reporting bundle findings for world peace",
    "observing humans buy bundles",
    "sending chichi secret sales data",
    "Waku waku mode: ENGAGED!"
]

def is_valid_bundle(entry):
    title = entry.title.lower()
    return any(keyword in title for keyword in ['bundle', 'software']) and not any(
        junk in title for junk in ['celebrating', 'donation', 'partnership', 'community', 'impact', 'support'])

def get_thumbnail(entry):
    if 'media_thumbnail' in entry:
        return entry.media_thumbnail[0]['url']
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    soup = BeautifulSoup(entry.get('summary', ''), 'html.parser')
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
            feed = feedparser.parse(requests.get(feed_url).content)
            for entry in feed.entries:
                if entry.title in posted_titles or not is_valid_bundle(entry):
                    continue
                posted_titles.add(entry.title)
                soup = BeautifulSoup(entry.get('summary', ''), 'html.parser')
                a = soup.find('a', href=True)
                bundle_link = a['href'] if a else entry.link

                embed = discord.Embed(
                    title=f"🎮 {entry.title}",
                    url=bundle_link,
                    color=discord.Color.orange() if 'humble' in source.lower() else discord.Color.red(),
                    timestamp=datetime.now()
                )
                summary = soup.get_text().strip()
                embed.add_field(name="📜 Summary", value=summary[:200] + '...' if len(summary) > 200 else summary, inline=False)

                thumb = get_thumbnail(entry)
                if thumb:
                    embed.set_image(url=thumb)

                embed.add_field(name="🔗 Blog Post", value=f"[More details]({entry.link})", inline=False)
                embed.set_footer(text=random.choice(anya_quotes))
                await channel.send(embed=embed)
                break
        except Exception as e:
            print(f"❌ Error with {source}: {e}")

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
        feed = feedparser.parse(requests.get(feed_url).content)
        for entry in feed.entries:
            if not is_valid_bundle(entry):
                continue

            soup = BeautifulSoup(entry.get('summary', ''), 'html.parser')
            a = soup.find('a', href=True)
            bundle_link = a['href'] if a else entry.link

            embed = discord.Embed(
                title=f"🎮 {entry.title}",
                url=bundle_link,
                color=discord.Color.orange() if 'humble' in source.lower() else discord.Color.red(),
                timestamp=datetime.now()
            )
            summary = soup.get_text().strip()
            embed.add_field(name="📜 Summary", value=summary[:200] + '...' if len(summary) > 200 else summary, inline=False)

            thumb = get_thumbnail(entry)
            if thumb:
                embed.set_image(url=thumb)

            embed.add_field(name="🔗 Blog Post", value=f"[More details]({entry.link})", inline=False)
            embed.set_footer(text=random.choice(anya_quotes))
            await ctx.send(embed=embed)
            return

    await ctx.send("Anya sees no new bundles right now~")

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

# --- Start Bot ---
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ DISCORD_TOKEN not found in environment.")
