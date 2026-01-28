from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

# ==========================================
# 0. ENUMS ( Match models.py EXACTLY)
# ==========================================

class PositionGroup(str, Enum):
    """
    Updated 6-Tier System.
    """
    GOALKEEPER = "Goalkeeper"
    CENTRE_BACK = "Centre-Back"
    FULL_BACK = "Full-Back"
    MIDFIELDER = "Midfielder"
    WINGER_AM = "Winger_AM"
    STRIKER = "Striker"

class CompetitionType(str, Enum):
    LEAGUE = "league"
    DOMESTIC_CUP = "domestic_cup"
    CONTINENTAL = "continental"
    INTERNATIONAL = "international"

# ==========================================
# 1. CORE ENTITIES (API Responses)
# ==========================================

class TeamResponse(BaseModel):
    id: int
    name: str
    country_name: str
    logo_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CountryResponse(BaseModel):
    id: int
    name: str
    iso_code: str
    flag_url: Optional[str] = None

# ==========================================
# 2. INGESTION SCHEMAS (For the Scraper)
# ==========================================

class MatchSnapshotCreate(BaseModel):
    """
    Represents one single game (Micro View).
    """
    date: date
    opponent_name: str
    competition_name: str
    minutes_played: int
    match_rating: Optional[float] = None
    stats: Dict[str, Any] = {} 

class PlayerSeasonStatCreate(BaseModel):
    """
    Represents a full season row (Macro View).
    Updated to include Tier 1 explicit columns.
    """
    season_name: str  # "2024-2025"
    competition_name: str
    team_name: str
    
    # Tier 1 Stats (Columns in DB)
    minutes: int
    goals: int = 0
    assists: int = 0
    xg: Optional[float] = None
    xa: Optional[float] = None
    rating: Optional[float] = None
    yellow_cards: int = 0
    red_cards: int = 0
    
    # Tier 2 Stats (JSONB Dump)
    detailed_stats: Dict[str, Any] = Field(default_factory=dict)

class TransferCreate(BaseModel):
    date: date
    from_team_name: str
    to_team_name: str
    fee_amount: float
    currency: str = "EUR"

class TeamMatchResultCreate(BaseModel):
    """
    For populating the League Knowledge Graph
    """
    date: date
    team_name: str
    opponent_name: str
    competition_name: str
    season_name: str
    
    goals_for: int
    goals_against: int
    is_home: bool = True
    is_neutral_venue: bool = False
    
    xg_for: Optional[float] = None
    xg_against: Optional[float] = None
    possession: Optional[float] = None

# ==========================================
# 3. THE MASTER SCRAPER OBJECT
# ==========================================

class PlayerScraperInput(BaseModel):
    """
    The "Bag" that holds everything found on a page.
    Updated to capture Physicals, Contracts, and Images.
    """
    name: str
    nationality_name: str
    birth_date: Optional[date] = None
    
    # New Scraping Fields
    height_cm: Optional[int] = None
    preferred_foot: Optional[str] = None
    image_url: Optional[str] = None
    contract_expiry: Optional[date] = None
    current_market_value: Optional[float] = None
    
    # Identifiers (Optional, mostly for cross-referencing)
    fotmob_id: Optional[int] = None
    transfermarkt_id: Optional[str] = None
    
    # Position Logic
    position_group: PositionGroup 
    specific_positions: List[str] = []
    
    # Nested Data
    season_stats: List[PlayerSeasonStatCreate] = []
    recent_matches: List[MatchSnapshotCreate] = []
    transfer_history: List[TransferCreate] = []

# ==========================================
# 4. API DASHBOARD RESPONSES
# ==========================================

class PlayerDashboardResponse(BaseModel):
    id: int
    name: str
    age: Optional[int] = None
    nationality: str
    image_url: Optional[str] = None # Added for UI
    
    team_name: str 
    position_group: PositionGroup
    specific_positions: List[str]
    
    height_cm: Optional[int] = None
    preferred_foot: Optional[str] = None
    
    current_gem_score: Optional[float]
    current_market_value: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)