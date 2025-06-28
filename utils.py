import discord
from datetime import datetime
from typing import List, Tuple
from models import PlayerInfo, ClanInfo

def get_rank_icon(rank: str) -> str:
    """Get the appropriate icon for a ProTanki rank"""
    rank_icons = {
        "Recruit": "🔸",
        "Private": "🔹", 
        "Gefreiter": "🔸🔹",
        "Corporal": "🔷",
        "Master Corporal": "🔷🔸",
        "Sergeant": "🔷🔷",
        "Staff Sergeant": "🔷🔷🔸",
        "Sergeant First Class": "🔷🔷🔷",
        "Master Sergeant": "🔶",
        "First Sergeant": "🔶🔸",
        "Sergeant Major": "🔶🔶",
        "Warrant Officer 1": "🔶🔶🔸",
        "Chief Warrant Officer 2": "🔶🔶🔶",
        "Chief Warrant Officer 3": "🔶🔶🔶🔸",
        "Chief Warrant Officer 4": "🔶🔶🔶🔶",
        "Chief Warrant Officer 5": "🔶🔶🔶🔶🔸",
        "Second Lieutenant": "🟨",
        "First Lieutenant": "🟨🔸",
        "Captain": "🟨🟨🟨🟨",
        "Major": "⭐",
        "Lieutenant Colonel": "⭐🔸",
        "Colonel": "⭐⭐",
        "Brigadier": "⭐⭐🔸",
        "Major General": "⭐⭐⭐",
        "Lieutenant General": "⭐⭐⭐🔸",
        "General": "⭐⭐⭐⭐",
        "Marshal": "👑",
        "Field Marshal": "👑🔸",
        "Commander": "👑👑",
        "Generalissimo": "👑👑👑"
    }
    return rank_icons.get(rank, "🔸")

def create_clan_embed(clan_name: str, members: List[Tuple], online_count: int, offline_count: int) -> discord.Embed:
    """Create a formatted embed for clan information"""
    
    embed = discord.Embed(
        title=f"🏆 Clan: {clan_name}",
        color=0x00ff00,  # Green color
        timestamp=datetime.utcnow()
    )
    
    # Add clan statistics
    total_members = len(members)
    embed.add_field(
        name="📊 Statistics",
        value=f"**Total Members:** {total_members}\n**Online:** {online_count} 🟢\n**Offline:** {offline_count} 🔴",
        inline=True
    )
    
    # Separate online and offline members
    online_members = []
    offline_members = []
    
    for member in members:
        status_icon = "🟢" if member.is_online else "🔴"
        member_info = f"{status_icon} **{member.username}**"
        
        if member.is_online:
            online_members.append(member_info)
        else:
            offline_members.append(member_info)
    
    # Add online members field
    if online_members:
        online_text = "\n".join(online_members[:10])  # Limit to 10 members per field
        if len(online_members) > 10:
            online_text += f"\n... and {len(online_members) - 10} more"
        embed.add_field(
            name="🟢 Online Members",
            value=online_text,
            inline=False
        )
    
    # Add offline members field
    if offline_members:
        offline_text = "\n".join(offline_members[:10])  # Limit to 10 members per field
        if len(offline_members) > 10:
            offline_text += f"\n... and {len(offline_members) - 10} more"
        embed.add_field(
            name="🔴 Offline Members",
            value=offline_text,
            inline=False
        )
    
    if not members:
        embed.add_field(
            name="👥 Members",
            value="No members in this clan yet.",
            inline=False
        )
    
    embed.set_footer(text="Last updated")
    
    return embed

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create an error embed"""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=0xff0000,  # Red color
        timestamp=datetime.utcnow()
    )
    return embed

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a success embed"""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=0x00ff00,  # Green color
        timestamp=datetime.utcnow()
    )
    return embed

def parse_jeffrie_user_response(response_content: str, username: str) -> PlayerInfo:
    """Parse the response from Jeffrie bot's /user command"""
    try:
        # Look for embed content in the response
        # This is a flexible parser that can handle various response formats
        
        # Default values
        rank = "Unknown"
        is_online = False
        
        # Check if the response contains online status indicators
        content_lower = response_content.lower()
        
        # Common online indicators
        online_indicators = ["online", "в сети", "active", "играет", "🟢"]
        offline_indicators = ["offline", "не в сети", "inactive", "🔴"]
        
        for indicator in online_indicators:
            if indicator in content_lower:
                is_online = True
                break
        
        # Extract rank information
        # Look for common rank patterns
        rank_patterns = [
            r"rank[:\s]+([^\n\r]+)",
            r"ранг[:\s]+([^\n\r]+)",
            r"звание[:\s]+([^\n\r]+)",
        ]
        
        import re
        for pattern in rank_patterns:
            match = re.search(pattern, content_lower)
            if match:
                rank = match.group(1).strip().title()
                break
        
        return PlayerInfo.from_jeffrie_response(response_content, username)
        
    except Exception as e:
        print(f"Error parsing Jeffrie response for {username}: {e}")
        return PlayerInfo(username=username, rank="Unknown", is_online=False)

class ClanSelectView(discord.ui.View):
    """View for clan selection dropdown"""
    
    def __init__(self, clans: List[Tuple[int, str]], callback_func):
        super().__init__(timeout=300)  # 5 minute timeout
        self.callback_func = callback_func
        
        # Create dropdown
        options = []
        for clan_id, clan_name in clans:
            options.append(discord.SelectOption(
                label=clan_name,
                value=str(clan_id),
                description=f"Select {clan_name}"
            ))
        
        if options:
            self.clan_select.options = options
        else:
            # Disable if no clans
            self.clan_select.disabled = True
            self.clan_select.options = [discord.SelectOption(
                label="No clans available",
                value="none"
            )]
    
    @discord.ui.select(
        placeholder="Choose a clan...",
        min_values=1,
        max_values=1
    )
    async def clan_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "none":
            await interaction.response.send_message(
                embed=create_error_embed("No Clans", "No clans are available."),
                ephemeral=True
            )
            return
        
        clan_id = int(select.values[0])
        await self.callback_func(interaction, clan_id)
