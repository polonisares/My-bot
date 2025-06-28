from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PlayerInfo:
    """Data class for player information from Jeffrie bot"""
    username: str
    rank: str
    is_online: bool
    level: Optional[int] = None
    experience: Optional[int] = None
    crystals: Optional[int] = None
    
    @classmethod
    def from_jeffrie_response(cls, response_text: str, username: str):
        """Parse Jeffrie bot response to extract player info"""
        # This will parse the response from Jeffrie bot's /user command
        # The actual format may vary, so this is a flexible parser
        
        is_online = "online" in response_text.lower() or "в сети" in response_text.lower()
        
        # Extract rank information
        rank = "Unknown"
        rank_keywords = ["rank", "ранг", "звание"]
        lines = response_text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            for keyword in rank_keywords:
                if keyword in line_lower:
                    # Extract rank from line
                    parts = line.split(':')
                    if len(parts) > 1:
                        rank = parts[1].strip()
                    break
        
        # Extract level if available
        level = None
        if "level" in response_text.lower() or "уровень" in response_text.lower():
            import re
            level_match = re.search(r'(?:level|уровень).*?(\d+)', response_text.lower())
            if level_match:
                level = int(level_match.group(1))
        
        return cls(
            username=username,
            rank=rank,
            is_online=is_online,
            level=level
        )

@dataclass
class ClanInfo:
    """Data class for clan information"""
    id: int
    name: str
    member_count: int
    online_count: int
    offline_count: int
    members: list
