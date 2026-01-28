from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

# --- Re-use Enums (Keep strict consistency with models.py) ---
class PositionGroup(str, Enum):
    GOALKEEPER = "Goalkeeper"
    DEFENDER = "Defender"
    MIDFIELDER = "Midfielder"
    ATTACKER = "Attacker"

class CompetitionType(str, Enum):
    LEAGUE = "league"
    DOMESTIC_CUP = "domestic_cup"
    CONTINENTAL = "continental"
    INTERNATIONAL = "international"

# ==========================================
# 1. CORE ENTITIES (Used for API Responses)
# ==========================================

class TeamResponse(BaseModel):
    id: int
    name: str
    country_name: str
    model_config = ConfigDict(from_attributes=True)

class CountryResponse(BaseModel):
    id: int
    name: str
    iso_code: str

# ==========================================
# 2. INGESTION SCHEMAS (For the Scraper)
# ==========================================

class MatchSnapshotCreate(BaseModel):
    """
    Represents one single game row from a website (e.g. FBref Match Log)
    """
    date: date
    opponent_name: str
    competition_name: str
    minutes_played: int
    match_rating: Optional[float] = None
    stats: Dict[str, Any] = {} # {"goals": 1, "xg": 0.4}

class PlayerSeasonStatCreate(BaseModel):
    """
    Represents a full season row (e.g. 'Premier League 24/25' table)
    """
    season_name: str  # "2024-2025"
    competition_name: str
    team_name: str
    
    minutes: int
    goals: int = 0
    assists: int = 0
    
    # Tier 1 Stats (xG, Progressive Carries, etc.) go here
    detailed_stats: Dict[str, Any] = Field(default_factory=dict)

class TransferCreate(BaseModel):
    date: date
    from_team_name: str
    to_team_name: str
    fee_amount: float
    currency: str = "EUR"

# ==========================================
# 3. THE MASTER SCRAPER OBJECT
# ==========================================

class PlayerScraperInput(BaseModel):
    """
    The Output of your Scraper.
    One object that contains EVERYTHING we found about a player on a page.
    """
    name: str
    nationality_name: str # e.g. "Spain" (We resolve to ID later)
    birth_date: Optional[date]
    
    # Position Logic
    # The scraper must calculate these before creating this object
    position_group: PositionGroup 
    specific_positions: List[str] = [] # ["RW", "RM"]
    
    # Nested Data
    season_stats: List[PlayerSeasonStatCreate] = []
    recent_matches: List[MatchSnapshotCreate] = []
    transfer_history: List[TransferCreate] = []

# ==========================================
# 4. API DASHBOARD RESPONSES
# ==========================================

class PlayerDashboardResponse(BaseModel):
    """
    What the Streamlit/Web Frontend receives
    """
    id: int
    name: str
    age: int # Calculated field in backend
    nationality: str
    
    team_name: str # Resolved from latest stats
    position_group: PositionGroup
    specific_positions: List[str]
    
    current_gem_score: Optional[float]
    current_market_value: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)