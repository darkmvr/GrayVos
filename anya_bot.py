"""
Discord bot implementation with basic commands and event handlers
Discord bundle bot implementation with RSS feed monitoring
"""
import discord
from discord.ext import commands
import feedparser
import asyncio
import logging
import os
from datetime import datetime
-120+78
# Configure logging
logger = logging.getLogger(__name__)
class DiscordBot(commands.Bot):
    """Main Discord bot class"""
# RSS Feed URLs
HUMBLE_RSS_URL = 'https://blog.humblebundle.com/rss/'
FANATICAL_RSS_URL = 'https://blog.fanatical.com/en/feed/'
class BundleBot(discord.Client):
    """Bundle monitoring Discord bot"""
    
    def __init__(self):
        # Configure bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        # Initialize bot with command prefix
        super().__init__(
            command_prefix=os.getenv('BOT_PREFIX', '!'),
            intents=intents,
            help_command=None
        )
        
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.posted_titles = set()
        self.start_time = datetime.now()
        
        self.channel_id = int(os.getenv('CHANNEL_ID', '1384937321555689642'))
    async def setup_hook(self):
        """Called when bot is ready to start background tasks"""
        self.bg_task = self.loop.create_task(self.check_feeds())
    async def on_ready(self):
        """Event handler for when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        logger.info(f'✅ Bundle Bot logged in as {self.user} (ID: {self.user.id})')
        logger.info(f'Bot is monitoring channel ID: {self.channel_id}')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="the server | !help"
            name="for new bundles"
        )
        await self.change_presence(activity=activity)
    async def check_feeds(self):
        """Background task to check RSS feeds for new bundles"""
        await self.wait_until_ready()
        channel = self.get_channel(self.channel_id)
        
    async def on_guild_join(self, guild):
        """Event handler for when bot joins a guild"""
        logger.info(f'Bot joined guild: {guild.name} (ID: {guild.id})')
        if not channel:
            logger.error(f"Could not find channel with ID: {self.channel_id}")
            return
        logger.info("Starting bundle monitoring...")
        
    async def on_guild_remove(self, guild):
        """Event handler for when bot leaves a guild"""
        logger.info(f'Bot left guild: {guild.name} (ID: {guild.id})')
        
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Command not found. Use `!help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        else:
            logger.error(f'Unhandled error in command {ctx.command}: {str(error)}')
            await ctx.send("❌ An error occurred while processing the command.")
            
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check bot latency"""
        latency = round(self.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: {latency}ms",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """Check bot uptime"""
        uptime_duration = datetime.now() - self.start_time
        days = uptime_duration.days
        hours, remainder = divmod(uptime_duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"Bot has been online for: {uptime_str}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
    @commands.command(name='info')
    async def info(self, ctx):
        """Display bot information"""
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.purple()
        )
        embed.add_field(name="Guilds", value=len(self.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.users), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.latency * 1000)}ms", inline=True)
        embed.add_field(name="Python Version", value="3.x", inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
        
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Display help information"""
        embed = discord.Embed(
            title="📋 Available Commands",
            description="Here are the available commands:",
            color=discord.Color.gold()
        )
        
        commands_list = [
            ("!ping", "Check bot latency"),
            ("!uptime", "Check bot uptime"),
            ("!info", "Display bot information"),
            ("!help", "Show this help message")
        ]
        
        for command, description in commands_list:
            embed.add_field(name=command, value=description, inline=False)
            
        embed.set_footer(text="Bot hosted on Replit with 24/7 uptime")
        await ctx.send(embed=embed)
        
    @commands.command(name='status')
    async def status(self, ctx):
        """Check bot status"""
        embed = discord.Embed(
            title="✅ Bot Status",
            description="Bot is online and operational!",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="🟢 Online", inline=True)
        embed.add_field(name="Hosting", value="Replit", inline=True)
        embed.add_field(name="Uptime Target", value="24/7", inline=True)
        
        await ctx.send(embed=embed)
        while not self.is_closed():
            try:
                feeds = [
                    (HUMBLE_RSS_URL, 'Humble Bundle'), 
                    (FANATICAL_RSS_URL, 'Fanatical')
                ]
                
                for feed_url, source in feeds:
                    try:
                        logger.info(f"Checking {source} feed...")
                        feed = feedparser.parse(feed_url)
                        
                        for entry in feed.entries:
                            if entry.title not in self.posted_titles:
                                self.posted_titles.add(entry.title)
                                
                                # Create embed for better formatting
                                embed = discord.Embed(
                                    title=f"🎮 New Bundle from {source}!",
                                    description=entry.title,
                                    url=entry.link,
                                    color=discord.Color.orange() if source == 'Humble Bundle' else discord.Color.red(),
                                    timestamp=datetime.now()
                                )
                                
                                if hasattr(entry, 'summary'):
                                    # Truncate summary if too long
                                    summary = entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary
                                    embed.add_field(name="Description", value=summary, inline=False)
                                
                                embed.set_footer(text=f"Bundle Alert • {source}")
                                
                                await channel.send(embed=embed)
                                logger.info(f"Posted new bundle: {entry.title}")
                                
                    except Exception as e:
                        logger.error(f"Error checking {source} feed: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error in feed checking loop: {str(e)}")
                
            # Wait 10 minutes before next check
            await asyncio.sleep(600)
def create_bundle_bot():
    """Create and return the bundle bot instance"""
    intents = discord.Intents.default()
    intents.message_content = True
    
    return BundleBot(intents=intents)
