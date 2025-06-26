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

# --- Flask keep-alive ---
app = Flask("")
@app.route("/")
def home():
    return random.choice([
        "Anya is alive and spying on bundles!",
        "Bundle intel secure. Anya online!",
        "Waku waku~! Anya is watching RSS feeds!"
    ]), 200

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()

# --- Bot setup ---
FEED_SOURCES = [
    ('https://blog.humblebundle.com/rss/', 'Humble Bundle RSS'),
    ('https://blog.fanatical.com/en/feed/', 'Fanatical RSS'),
    ('https://www.reddit.com/r/Gamebundles/.rss', 'Reddit Gamebundles'),
    ('https://www.reddit.com/r/humblebundles/.rss', 'Reddit Humblebundles'),
]

INT_JSON_URL = 'https://www.humblebundle.com/client/bundles'

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default(), help_command=None)
posted = set()
channel_id = int(os.getenv('CHANNEL_ID'))
start_time = datetime.now()

# --- Anya quotes (extended) ---
anya_quotes = [
    "Anya found this bundle! Waku waku~~! 🥜",
    "Anya spy mission: deliver new games. Success! 👀",
    "Hehe~ ちち would buy this for sure.",
    "Yor would smash if no one buys this one!",
    "Anya read minds and this one looked good!",
    "Loid-san would approve this deal!",
    "For the mission... for the fun... for the peanuts~",
    "Loid doesn't know I posted this hehe~",
    "Waku waku~! Buy this or face peanut wrath!",
    "Even Chimera-san approves this one~",
    "Bond says this bundle smells like adventure!",
    "This one made Anya's face go (⊙﹏⊙)",
    "Mission success rate: 100% for bundles!",
    "Anya predicts... you're gonna click this!",
    "Spy tools? No, Anya uses bundles!",
    "Bundle intel delivered to haha and chichi.",
    "This is a bundle only a spy could love!",
    "Anya used her telepathy. This is a good one!",
    "Anya’s danger meter says: BUY NOW!",
    "Waku waku energy: off the charts today!",
    "Anya totally didn’t press random buttons~",
    "Bundle detected! Anya’s spy sense tingled!",
    "Secret sale... revealed by Agent Anya!",
    "Anya says: it’s bundle time!",
    "Peanut-powered bundle recommendation!",
    "Buying this bundle increases stealth stat!",
    "Hmmm yes. Very bundle. Very wow.",
    "No lie detector needed — this bundle rocks!",
    "Bundle smells like happiness and peanut butter!",
    "Waku waku! This one's top-tier!"
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
    title = entry.get('title','').lower()
    return 'bundle' in title or 'software' in title

def get_thumbnail(entry):
    for key in ('media_thumbnail','media_content'):
        if key in entry:
            return entry[key][0].get('url')
    soup = BeautifulSoup(entry.get('summary',''),'html.parser')
    img = soup.find('img')
    return img['src'] if img else None

def extract_direct_link_humble():
    try:
        resp = requests.get(INT_JSON_URL, timeout=10)
        data = resp.json().get('bundles',[])
        for b in data:
            if b.get('visible') and b.get('bundle') and b.get('humanized_end_at'):
                return b['details_url']
    except Exception as e:
        print("❌ JSON endpoint failed:", e)
    return None

def extract_direct_link(post_url):
    if 'humblebundle.com/blog' in post_url:
        link = extract_direct_link_humble()
        if link:
            return link
    try:
        resp = requests.get(post_url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        a = soup.find('a', href=True, string=lambda s: s and ('bundle' in s.lower() or 'store' in s.lower()))
        if a: return a['href']
    except Exception as e:
        print("❌ Post parse failed:", e)
    return post_url

@bot.event
async def on_ready():
    print(f"✅ Anya connected as {bot.user}")
    await bot.change_presence(activity=discord.Game(random.choice(anya_statuses)))
    check_feeds.start()

@tasks.loop(minutes=10)
async def check_feeds():
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"❌ Invalid channel: {channel_id}")
        return

    for url, src in FEED_SOURCES:
        try:
            resp = requests.get(url, timeout=10)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                if entry.get('title') in posted or not is_valid_bundle(entry):
                    continue
                posted.add(entry.title)

                thumb = get_thumbnail(entry)
                link = extract_direct_link(entry.link)
                embed = discord.Embed(
                    title=f"🎮 {entry.title}",
                    url=link,
                    color=discord.Color.orange() if 'humble' in src.lower() else discord.Color.red(),
                    timestamp=datetime.now()
                )
                summary = BeautifulSoup(entry.get('summary',''), 'html.parser').get_text()
                embed.add_field(name="📝 Summary", value=summary[:200]+'...' if len(summary)>200 else summary, inline=False)
                if thumb: embed.set_image(url=thumb)
                embed.add_field(name="🔗 Blog", value=f"[Read full post]({entry.link})", inline=False)
                embed.set_footer(text=random.choice(anya_quotes))
                await channel.send(embed=embed)
                break
        except Exception as e:
            print(f"❌ Feed error {src}: {e}")

@bot.command()
async def latestbundle(ctx):
    try:
        link = extract_direct_link_humble()
        if link:
            await ctx.send(f"🎮 Direct Humble bundle link: {link}")
            return

        for url, src in FEED_SOURCES:
            resp = requests.get(url, timeout=10)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                if is_valid_bundle(entry):
                    thumb = get_thumbnail(entry)
                    link = extract_direct_link(entry.link)
                    embed = discord.Embed(
                        title=f"🎮 {entry.title}",
                        url=link,
                        color=discord.Color.orange() if 'humble' in src.lower() else discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    summary = BeautifulSoup(entry.get('summary',''), 'html.parser').get_text()
                    embed.add_field(name="📝 Summary", value=summary[:200]+'...' if len(summary)>200 else summary, inline=False)
                    if thumb: embed.set_image(url=thumb)
                    embed.set_footer(text=random.choice(anya_quotes))
                    await ctx.send(embed=embed)
                    return
        await ctx.send("🕵️ Anya didn't find any bundles right now, try again later!")
    except Exception as e:
        print("❌ Error in latestbundle:", e)
        await ctx.send("😖 Anya had trouble spying the latest bundle!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Anya brain ping: {round(bot.latency * 1000)}ms")

@bot.command()
async def uptime(ctx):
    up = str(datetime.now() - start_time).split('.')[0]
    await ctx.send(f"⏰ Anya spying since: {up}")

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

bot.run(os.getenv('DISCORD_TOKEN'))
