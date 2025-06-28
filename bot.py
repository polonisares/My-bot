import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from database import db
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

class ProTankiBot(commands.Bot):
    """Main bot class for ProTanki clan management"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            application_id=None  # Discord will auto-detect
        )
    
    async def setup_hook(self):
        """Called when the bot is starting up"""
        print("Setting up ProTanki Bot...")
        
        # Initialize database
        await db.initialize()
        print("Database initialized")
        
        # Load cogs
        try:
            await self.load_extension("commands")
            print("Commands cog loaded")
        except Exception as e:
            print(f"Failed to load commands cog: {e}")
        
        # Sync slash commands globally and for each guild
        try:
            # Global sync
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} global command(s)")
            
            # Sync for each guild individually to ensure immediate availability
            for guild in self.guilds:
                try:
                    guild_synced = await self.tree.sync(guild=guild)
                    print(f"Synced {len(guild_synced)} command(s) for guild: {guild.name}")
                except Exception as guild_error:
                    print(f"Failed to sync commands for guild {guild.name}: {guild_error}")
                    
        except Exception as e:
            print(f"Failed to sync global commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        print(f"{self.user} has connected to Discord!")
        print(f"Bot is in {len(self.guilds)} guild(s)")
        
        # Force sync commands for all guilds when ready
        for guild in self.guilds:
            try:
                # Clear existing commands first
                self.tree.clear_commands(guild=guild)
                # Copy global commands to guild
                self.tree.copy_global_to(guild=guild)
                # Sync guild commands
                guild_synced = await self.tree.sync(guild=guild)
                print(f"Force synced {len(guild_synced)} command(s) for guild: {guild.name}")
                
                # List the synced commands
                for cmd in guild_synced:
                    print(f"  - {cmd.name}: {cmd.description}")
                    
            except Exception as guild_error:
                print(f"Failed to force sync commands for guild {guild.name}: {guild_error}")
                
        # Also check bot permissions
        for guild in self.guilds:
            if self.user:
                bot_member = guild.get_member(self.user.id)
                if bot_member:
                    perms = bot_member.guild_permissions
                    print(f"Bot permissions in {guild.name}:")
                    print(f"  - Use Application Commands: {perms.use_application_commands}")
                    print(f"  - Send Messages: {perms.send_messages}")
                    print(f"  - Embed Links: {perms.embed_links}")
                    print(f"  - Administrator: {perms.administrator}")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="ProTanki clans"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a guild"""
        print(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Try to sync commands for this guild
        try:
            await self.tree.sync(guild=guild)
            print(f"Synced commands for guild: {guild.name}")
        except Exception as e:
            print(f"Failed to sync commands for guild {guild.name}: {e}")
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        print(f"Command error: {error}")
    
    async def on_application_command_error(self, interaction: discord.Interaction, error):
        """Handle application command errors"""
        print(f"Application command error: {error}")
        
        if not interaction.response.is_done():
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while processing your command. Please try again later.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def main():
    """Main function to run the bot"""
    
    # Check for required environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        print("Please create a .env file with your Discord bot token")
        return
    
    bot_owner_id = os.getenv("BOT_OWNER_ID")
    if not bot_owner_id:
        print("Warning: BOT_OWNER_ID not set. /addclan command will not work")
    
    jeffrie_bot_id = os.getenv("JEFFRIE_BOT_ID")
    if not jeffrie_bot_id:
        print("Warning: JEFFRIE_BOT_ID not set. Player monitoring may not work properly")
    
    # Create and run bot
    bot = ProTankiBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\nShutting down bot...")
    except discord.LoginFailure:
        print("Error: Invalid Discord token")
    except Exception as e:
        print(f"Error running bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot shutdown complete")
