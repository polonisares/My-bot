import discord
from discord.ext import commands
from discord import app_commands
from database import db, Member
from utils import create_clan_embed, create_error_embed, create_success_embed, ClanSelectView
from monitoring import PlayerMonitor
import os

class ClanCommands(commands.Cog):
    """Cog containing all clan management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.bot_owner_id = int(os.getenv("BOT_OWNER_ID", "0"))
        self.monitor = PlayerMonitor(bot)
    
    async def cog_load(self):
        """Called when the cog is loaded"""
        await self.monitor.start_monitoring()
    
    async def cog_unload(self):
        """Called when the cog is unloaded"""
        await self.monitor.stop_monitoring()
    
    @app_commands.command(name="addclan", description="Add a new clan (Owner only)")
    @app_commands.describe(name="The name of the clan to create")
    async def add_clan(self, interaction: discord.Interaction, name: str):
        """Add a new clan - restricted to bot owner"""
        
        # Check if user is bot owner
        if interaction.user.id != self.bot_owner_id:
            embed = create_error_embed(
                "Permission Denied",
                "Only the bot owner can create new clans."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate clan name
        if len(name) < 2 or len(name) > 50:
            embed = create_error_embed(
                "Invalid Clan Name",
                "Clan name must be between 2 and 50 characters."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add clan to database
        success = await db.add_clan(name)
        
        if success:
            embed = create_success_embed(
                "Clan Created",
                f"Successfully created clan **{name}**!"
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = create_error_embed(
                "Clan Creation Failed",
                f"Clan **{name}** already exists or there was an error creating it."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="addmember", description="Add a ProTanki player to a clan")
    @app_commands.describe(username="The ProTanki username to add")
    async def add_member(self, interaction: discord.Interaction, username: str):
        """Add a member to a clan with clan selection"""
        
        # Validate username
        if len(username) < 2 or len(username) > 30:
            embed = create_error_embed(
                "Invalid Username",
                "Username must be between 2 and 30 characters."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get available clans
        clans = await db.get_clans()
        
        if not clans:
            embed = create_error_embed(
                "No Clans Available",
                "No clans have been created yet. Ask the bot owner to create one first."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create clan selection callback
        async def clan_selected(select_interaction: discord.Interaction, clan_id: int):
            # Acknowledge the interaction immediately to prevent timeout
            await select_interaction.response.defer()
            
            # Add member to selected clan
            success = await db.add_member(username, clan_id)
            
            if success:
                # Get real player info immediately using our scraper
                try:
                    # Use a dummy channel for the scraper since we don't actually need it
                    player_info = await self.monitor.force_check_player(username, None)
                    embed = create_success_embed(
                        "Member Added",
                        f"Successfully added **{username}** to the clan!\n"
                        f"Status: {'🟢 Online' if player_info.is_online else '🔴 Offline'}"
                    )
                except Exception as e:
                    print(f"Error getting player info: {e}")
                    embed = create_success_embed(
                        "Member Added",
                        f"Successfully added **{username}** to the clan!\n"
                        f"Player status will be updated shortly."
                    )
                await select_interaction.edit_original_response(embed=embed, view=None)
            else:
                embed = create_error_embed(
                    "Failed to Add Member",
                    f"**{username}** is already in a clan or there was an error adding them."
                )
                await select_interaction.edit_original_response(embed=embed, view=None)
        
        # Create and send clan selection view
        view = ClanSelectView(clans, clan_selected)
        
        embed = discord.Embed(
            title="🏆 Select Clan",
            description=f"Choose which clan to add **{username}** to:",
            color=0x0099ff
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="removemember", description="Remove a member from their clan")
    @app_commands.describe(username="ProTanki username to remove from clan")
    async def remove_member(self, interaction: discord.Interaction, username: str):
        """Remove a member from their clan"""
        await interaction.response.defer()
        
        # Get database instance
        db = self.bot.db
        
        # Find the member
        session = db.get_session()
        try:
            member = session.query(Member).filter(Member.username == username).first()
            
            if not member:
                embed = create_error_embed(
                    "Member Not Found",
                    f"**{username}** is not in any clan."
                )
                await interaction.followup.send(embed=embed)
                return
            
            clan_name = member.clan.name
            
            # Remove the member
            session.delete(member)
            session.commit()
            
            embed = create_success_embed(
                "Member Removed",
                f"Successfully removed **{username}** from **{clan_name}**."
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            session.rollback()
            print(f"Error removing member: {e}")
            embed = create_error_embed(
                "Error",
                "Failed to remove member. Please try again."
            )
            await interaction.followup.send(embed=embed)
        finally:
            session.close()

    @app_commands.command(name="removeclan", description="Remove a clan (Owner only)")
    @app_commands.describe(name="Name of the clan to remove")
    async def remove_clan(self, interaction: discord.Interaction, name: str):
        """Remove a clan - restricted to bot owner"""
        await interaction.response.defer()
        
        # Check if user has permission (bot owner only)
        if interaction.user.id != int(os.getenv('BOT_OWNER_ID')):
            embed = create_error_embed(
                "Permission Denied", 
                "Only the bot owner can remove clans."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get database instance
        db = self.bot.db
        
        # Remove the clan
        success = await db.remove_clan(name)
        
        if success:
            embed = create_success_embed(
                "Clan Removed",
                f"Successfully removed clan **{name}** and all its members."
            )
        else:
            embed = create_error_embed(
                "Clan Not Found",
                f"Clan **{name}** does not exist."
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="viewclan", description="View clan information and member status")
    async def view_clan(self, interaction: discord.Interaction):
        """View clan information with member status"""
        
        # Get available clans
        clans = await db.get_clans()
        
        if not clans:
            embed = create_error_embed(
                "No Clans Available",
                "No clans have been created yet."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create clan selection callback
        async def clan_selected(select_interaction: discord.Interaction, clan_id: int):
            # Acknowledge the interaction immediately to prevent timeout
            await select_interaction.response.defer()
            
            # Get clan and members
            clan, members = await db.get_clan_members(clan_id)
            
            if not clan:
                embed = create_error_embed(
                    "Clan Not Found",
                    "The selected clan could not be found."
                )
                await select_interaction.edit_original_response(embed=embed, view=None)
                return
            
            # Count online/offline members
            online_count = sum(1 for member in members if member.is_online)
            offline_count = len(members) - online_count
            
            # Create clan info embed
            embed = create_clan_embed(clan.name, members, online_count, offline_count)
            
            await select_interaction.edit_original_response(embed=embed, view=None)
        
        # Create and send clan selection view
        view = ClanSelectView(clans, clan_selected)
        
        embed = discord.Embed(
            title="🏆 Select Clan to View",
            description="Choose which clan to view:",
            color=0x0099ff
        )
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(ClanCommands(bot))
