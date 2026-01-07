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
import asyncio
import yt_dlp

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

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# --- Discord bot ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Needed to detect voice channels
bot = commands.Bot(command_prefix='!', intents=intents)

FEED_SOURCES = [
    ('https://blog.humblebundle.com/rss/', 'Humble Bundle'),
    ('https://blog.fanatical.com/en/feed/', 'Fanatical'),
]

posted_titles = set()
channel_id = int(os.getenv('CHANNEL_ID'))

anya_quotes = [
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

anya_music_quotes = [
    "Waku waku~! Music makes Anya brain go brrr~ 🎶",
    "Anya likes this song! Peanut rhythm detected! 🥜",
    "Hehe~ chichi would tap foot to this one!",
    "This song is VERY spy approved 🕵️‍♀️🎧",
    "Anya feels smart listening to this music!",
    "Music makes mission easier! Probably!",
    "Waku waku~! This song has main character energy!",
    "Anya dance time! Nobody look! 💃",
    "Even Bond is vibing right now 🐶🎶",
    "This song makes Anya feel like secret agent!",
    "Hehe~ Anya pressed play. Good button.",
    "Anya thinks this song is cool. Very cool.",
    "Spy HQ background music activated 🎧",
    "This music makes peanuts taste better 🥜✨",
    "Anya heard this in chichi’s head!",
    "Waku waku overload! Volume in heart increased!",
    "This song = +10 spy power!",
    "Anya would save this to playlist if Anya had one!",
    "Music so good even lie detector says TRUE!",
    "Anya approves this vibe! 👍",
    "This song smells like adventure!",
    "Hehe~ Anya nodding head like grown-up!",
    "Anya calls this… a bop.",
    "Mission update: vibes are excellent!",
    "If this song was homework, Anya would do it!"
]

# --- Events ---
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("spying on game deals 👀"))
    print(f"✅ Anya has connected as {bot.user}")
    check_feeds.start()

# --- RSS feed commands ---
@bot.command()
async def latestbundle(ctx):
    found = await post_all_bundles(ctx.send)
    if not found:
        await ctx.send("Anya sees no new bundles right now~")

@tasks.loop(minutes=10)
async def check_feeds():
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"❌ Could not find channel with ID {channel_id}")
        return
    await post_all_bundles(channel.send)

async def post_all_bundles(post_func):
    found = False
    for feed_url, source in FEED_SOURCES:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if entry.title in posted_titles:
                continue
            if not looks_like_bundle(entry):
                continue
            posted_titles.add(entry.title)
            embed = build_bundle_embed(entry, source)
            await post_func(embed=embed)
            found = True

    # GG.deals scraping
    gg_bundles = fetch_gg_deals_bundles()
    for bundle in gg_bundles:
        if bundle["title"] in posted_titles:
            continue
        posted_titles.add(bundle["title"])
        embed = discord.Embed(
            title=f"🎮 New GG.deals Bundle!",
            description=bundle["title"],
            url=bundle["url"],
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        if bundle["thumb"]:
            embed.set_image(url=bundle["thumb"])
        embed.set_footer(text=random.choice(anya_quotes))
        await post_func(embed=embed)
        found = True
    return found

def looks_like_bundle(entry):
    title = entry.title.lower()
    summary = getattr(entry, 'summary', '').lower()
    keywords = ["bundle", "choice", "software", "deal", "pack", "build your own"]
    return any(kw in title or kw in summary for kw in keywords)

def build_bundle_embed(entry, source):
    embed = discord.Embed(
        title=f"🎮 New {source} Bundle!",
        description=entry.title,
        url=entry.link,
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    summary = get_summary(entry)
    if summary:
        embed.add_field(name="📝 Summary", value=summary, inline=False)
    thumb = get_thumbnail(entry.link)
    if thumb:
        embed.set_image(url=thumb)
    embed.set_footer(text=random.choice(anya_quotes))
    return embed

def get_summary(entry):
    if hasattr(entry, 'summary'):
        clean = BeautifulSoup(entry.summary, 'html.parser').get_text()
        return clean[:200] + "..." if len(clean) > 200 else clean
    return None

def get_thumbnail(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        img = soup.find("meta", property="og:image")
        if img and img.get("content"):
            return img["content"]
        fallback_img = soup.find("img")
        if fallback_img and fallback_img.get("src"):
            return fallback_img["src"]
    except Exception as e:
        print(f"Thumbnail fetch failed for {url}: {e}")
    return None

def fetch_gg_deals_bundles():
    try:
        resp = requests.get("https://gg.deals/news/bundles/", timeout=10)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        articles = soup.find_all("div", class_="news-title")
        bundles = []
        for article in articles:
            a_tag = article.find("a")
            if not a_tag:
                continue
            title = a_tag.text.strip()
            url = "https://gg.deals" + a_tag['href']
            thumb = get_thumbnail(url)
            bundles.append({"title": title, "url": url, "thumb": thumb})
        return bundles
    except Exception as e:
        print(f"Failed to fetch GG.deals: {e}")
        return []

# --- Anya voice/music/watch commands ---
@bot.command(name="anya")
async def anya_voice(ctx, mode: str = None, *, query: str = None):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Anya says: join voice first! 😤")
        return

    voice_channel = ctx.author.voice.channel

    if mode is None:
        await ctx.send(
            "**Anya voice commands:**\n"
            "`!anya watch` → YouTube Watch Together 📺\n"
            "`!anya play <song>` → play music 🎵\n"
            "`!anya stop` → stop music ⛔"
        )
        return

    # 📺 WATCH TOGETHER
    if mode.lower() == "watch":
        invite = await voice_channel.create_invite(
            target_application_id=880218394199220334,
            target_type=2,
            max_age=0
        )
        await ctx.send(f"📺 **Anya starts YouTube time!**\n👉 {invite.url}")
        return

    # 🎵 PLAY MUSIC
    if mode.lower() == "play":
        if not query:
            await ctx.send("Anya needs a song to play! 😠")
            return

        if ctx.voice_client is None:
            try:
                vc = await voice_channel.connect()
            except Exception as e:
                await ctx.send(f"Anya failed to join voice: {e}")
                return
        else:
            vc = ctx.voice_client
            if vc.channel != voice_channel:
                await vc.move_to(voice_channel)

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "default_search": "ytsearch",
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            url = info["url"]
            title = info.get("title", "Unknown")

        vc.play(discord.FFmpegPCMAudio(url), after=lambda e: print(f"Audio ended: {e}"))
        await ctx.send(f"🎶 **Anya plays:** {title} ♪\n{random.choice(anya_music_quotes)}")
        return

    # ⛔ STOP
    if mode.lower() == "stop":
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send(random.choice([
                "🛑 Music stopped! Back to spy work 😌",
                "Anya pressed stop. Mission paused.",
                "No more music… Anya sad now 😔",
                "Silence activated! Spy mode engaged!",
                "Music nap time over!"
            ]))
        else:
            await ctx.send("Anya wasn't playing anything~")
        return

    await ctx.send(f"Unknown mode `{mode}`. Type `!anya` to see available commands.")

# --- Join/Leave commands ---
@bot.command(name="anyajoin")
async def anya_join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Anya says: you need to be in a voice channel first! 😤")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        try:
            vc = await voice_channel.connect()
            await ctx.send(f"Anya joins {voice_channel.name}! 🎶")
        except Exception as e:
            await ctx.send(f"Anya failed to join: {e}")
    else:
        vc = ctx.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)
            await ctx.send(f"Anya moves to {voice_channel.name} 🕵️‍♀️")
        else:
            await ctx.send("Anya is already in your voice channel! 😎")

@bot.command(name="anyaleave")
async def anya_leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Anya leaves the voice channel. Bye bye~ 👋")
    else:
        await ctx.send("Anya isn't in any voice channel right now~ 😢")

# --- Run bot ---
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Missing DISCORD_TOKEN!")
else:
    bot.run(token)
