import discord
from discord.ext import commands, tasks
import requests
import os
import random
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
        "Waku waku~! Anya is watching deals!",
        "Anya is doing important spy work rn~ 🕵️‍♀️"
    ]), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# --- Discord bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Your IsThereAnyDeal API key
ITAD_API_KEY = os.getenv('ITAD_API_KEY')

# Keep track of posted bundle IDs
posted_bundle_ids = set()
channel_id = int(os.getenv('CHANNEL_ID'))

anya_quotes = [
    # Your existing quotes here, keep as-is!
    "Anya found this bundle! Waku waku~~! 🥜",
    "Anya spy mission: deliver new games. Success! 👀",
    "Oooh, Anya thinks you might like this one!",
    "This bundle smells like peanuts and fun. 🥜",
    "Hehe~ chichi would buy this for sure.",
    "New games = more friends = world peace!",
    "Anya read minds and this one looked good!",
    "Waku waku~! Another bundle spotted!",
    "This one... has Anya vibes~",
    "Heh! Anya is best bundle spy!",
    "Spy report complete! Bundle delivered.",
    "Your mission is to click this bundle! 🕵️",
    "chichi would approve this deal!",
    "For the mission... for the fun... for the peanuts~",
    "Ooooooh! Shiny bundle!",
    "Hehe~ Anya pressed the button. Good button.",
    "Waku waku~! Anya did something useful!",
    "Hah! Anya's spy senses were tingling!",
    "Twilight would say this is 'efficient'!",
    "Bond says this bundle has good vibes.",
    "haha would smash if no one buys this one!",
    "Anya detected value... 10/10 mission success!",
    "More games = less homework, right? 😈",
    "Waku waku~! Buy this or face peanut wrath!",
    "Shhh... secret bundle intel! 🤫",
    "Waku waku overload! This bundle is top tier~",
    "This deal made Anya's face go ⊙﹏⊙",
    "chichi doesn't know I posted this hehe~",
    "Why does bundle smell like... victory?",
    "Bundle detected! Waku waku alert~",
    "Hmm... yes. Very bundle. Very wow~",
    "This deal smells like spy success 🕶️",
    "No lie detector needed—this bundle is good!",
    "Even Chimera-san approves this one~"
]

def fetch_bundles():
    """
    Calls IsThereAnyDeal API to fetch current active bundles from Humble and Fanatical stores.
    Returns a list of bundles (dicts with info).
    """
    url = "https://api.isthereanydeal.com/v01/deals/bundles/"
    params = {
        'key': ITAD_API_KEY,
        'region': 'us',
        'country': 'US',
        'limit': 10,
        'store': 'humble,fanatical',  # comma-separated list of stores to filter
        'sort': 'added',  # newest first
        'hideinactive': 1,
        'bundlestate': 'active'
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if 'data' in data and 'bundles' in data['data']:
            return data['data']['bundles']
    except Exception as e:
        print(f"Failed to fetch bundles from ITAD: {e}")
    return []

def build_bundle_embed(bundle):
    """
    Builds a Discord embed for a bundle dictionary from ITAD API.
    """
    title = bundle.get('title', 'Unknown Bundle')
    url = bundle.get('url', '')
    thumb = bundle.get('image', None)
    added_ts = bundle.get('added', None)
    timestamp = datetime.fromtimestamp(added_ts) if added_ts else datetime.now()

    embed = discord.Embed(
        title=f"🎮 New Bundle: {title}",
        url=url,
        color=discord.Color.orange(),
        timestamp=timestamp
    )
    if thumb:
        embed.set_thumbnail(url=thumb)
    embed.set_footer(text=random.choice(anya_quotes))
    return embed

@tasks.loop(minutes=10)
async def check_itad_bundles():
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"Could not find channel with ID {channel_id}")
        return

    bundles = fetch_bundles()
    if not bundles:
        print("No bundles found from ITAD.")
        return

    for bundle in bundles:
        bundle_id = bundle.get('id')
        if not bundle_id or bundle_id in posted_bundle_ids:
            continue

        posted_bundle_ids.add(bundle_id)
        embed = build_bundle_embed(bundle)
        await channel.send(embed=embed)
        # Only send one bundle per check to avoid spamming
        return

@bot.event
async def on_ready():
    print(f"✅ Anya has connected as {bot.user}")
    check_itad_bundles.start()

@bot.command()
async def latestbundle(ctx):
    bundles = fetch_bundles()
    for bundle in bundles:
        if bundle.get('id') in posted_bundle_ids:
            continue
        posted_bundle_ids.add(bundle.get('id'))
        embed = build_bundle_embed(bundle)
        await ctx.send(embed=embed)
        return
    await ctx.send("Anya sees no new bundles right now~")

# --- Run bot ---
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Missing DISCORD_TOKEN!")
else:
    bot.run(token)
