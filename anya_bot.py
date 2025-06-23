import asyncio
import datetime
import time
import calendar

import feedparser
import hikari
import lightbulb

# --- Configuration --- #
TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot's token
PREFIX = "!"
# RSS feed URLs
HUMBLE_RSS_URL = "https://blog.humblebundle.com/rss"
FANATICAL_RSS_URL = "https://steamcommunity.com/groups/wearefanatical/rss"

# Discord channel IDs to post the bundles
# You should replace these with your actual channel IDs
HUMBLE_CHANNEL_ID = 123456789012345678  # Channel for Humble Bundle posts
FANATICAL_CHANNEL_ID = 234567890123456789  # Channel for Fanatical posts

# --- Bot Setup --- #
bot = lightbulb.BotApp(
    token=TOKEN,
    prefix=PREFIX,
    intents=hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT
)

def _get_entry_datetime(entry):
    """Return the datetime of a feed entry using updated or published time (UTC)."""
    dt = None
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        # Use calendar.timegm to treat struct_time as UTC
        ts = calendar.timegm(entry.updated_parsed)
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    elif hasattr(entry, 'published_parsed') and entry.published_parsed:
        ts = calendar.timegm(entry.published_parsed)
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    return dt

async def _process_feed(feed_url, channel_id):
    """
    Parse the given RSS feed and post new entries (within 7 days) to the specified channel.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    threshold = now - datetime.timedelta(days=7)
    feed = feedparser.parse(feed_url)
    if not feed or not hasattr(feed, 'entries'):
        return
    for entry in feed.entries:
        entry_dt = _get_entry_datetime(entry)
        # Skip if entry has no date or is older than 7 days
        if not entry_dt or entry_dt < threshold:
            continue
        title = entry.title
        link = entry.link
        description = entry.get('summary', '') or entry.get('description', '')
        embed = hikari.Embed(title=title, url=link, description=description)
        # If the entry has an image, set as thumbnail
        image_url = None
        if 'media_thumbnail' in entry:
            image = entry.media_thumbnail
            if isinstance(image, list) and image:
                image_url = image[0].get('url')
        elif 'media_content' in entry:
            media = entry.media_content
            if isinstance(media, list) and media:
                image_url = media[0].get('url')
        if not image_url and 'links' in entry:
            for link_item in entry.links:
                if link_item.get('rel') == 'enclosure' and link_item.get('type', '').startswith('image'):
                    image_url = link_item.get('href')
                    break
        if image_url:
            embed.set_thumbnail(image_url)
        try:
            await bot.rest.create_message(channel_id, embed=embed)
        except Exception:
            pass

async def _bundle_feed_loop():
    """
    Background task that periodically checks RSS feeds for new bundles.
    """
    await bot.wait_until_started()
    while True:
        await _process_feed(HUMBLE_RSS_URL, HUMBLE_CHANNEL_ID)
        await _process_feed(FANATICAL_RSS_URL, FANATICAL_CHANNEL_ID)
        # Check every hour
        await asyncio.sleep(3600)

@bot.listen(hikari.StartedEvent)
async def on_bot_started(event):
    bot.create_task(_bundle_feed_loop())

@bot.command
@lightbulb.command('latestbundle', 'Get the latest bundle from Humble and Fanatical (last 7 days)')
@lightbulb.implements(lightbulb.PrefixCommand)
async def latestbundle(ctx: lightbulb.Context) -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    threshold = now - datetime.timedelta(days=7)
    latest_entries = []
    for feed_url in (HUMBLE_RSS_URL, FANATICAL_RSS_URL):
        feed = feedparser.parse(feed_url)
        if not feed or not hasattr(feed, 'entries'):
            continue
        for entry in feed.entries:
            entry_dt = _get_entry_datetime(entry)
            if not entry_dt or entry_dt < threshold:
                continue
            latest_entries.append(entry)
            break  # Only take the newest entry from each feed
    if not latest_entries:
        await ctx.respond("No bundles found from the last 7 days.")
        return
    for entry in latest_entries:
        title = entry.title
        link = entry.link
        description = entry.get('summary', '') or entry.get('description', '')
        embed = hikari.Embed(title=title, url=link, description=description)
        image_url = None
        if 'media_thumbnail' in entry:
            image = entry.media_thumbnail
            if isinstance(image, list) and image:
                image_url = image[0].get('url')
        elif 'media_content' in entry:
            media = entry.media_content
            if isinstance(media, list) and media:
                image_url = media[0].get('url')
        if not image_url and 'links' in entry:
            for link_item in entry.links:
                if link_item.get('rel') == 'enclosure' and link_item.get('type', '').startswith('image'):
                    image_url = link_item.get('href')
                    break
        if image_url:
            embed.set_thumbnail(image_url)
        await ctx.respond(embed=embed)

if __name__ == "__main__":
    bot.run()
