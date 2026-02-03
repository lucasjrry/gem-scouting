from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum as PyEnum

# ==========================================
# Pydantic enums matching SQLAlchemy models
# ==========================================

class CompetitionType(str, PyEnum):
    LEAGUE = "league"
    DOMESTIC_CUP = "domestic_cup"
    CONTINENTAL = "continental"
    INTERNATIONAL = "international"

class PositionGroup(str, PyEnum):
    GOALKEEPER = "Goalkeeper"
    CENTRE_BACK = "Centre-Back"
    FULL_BACK = "Full-Back"
    MIDFIELDER = "Midfielder"
    WINGER_AM = "Winger_AM"
    STRIKER = "Striker"

class InternationalLevel(str, PyEnum):
    SENIOR = "Senior"
    U23 = "U23" # Olympic
    U21 = "U21"
    U20 = "U20"
    U19 = "U19"
    U18 = "U18"
    U17 = "U17"
    U16 = "U16"
    U15 = "U15"


# ==========================================
# Core response / read schemas (mirror DB columns)
# ==========================================

class CountryResponse(BaseModel):
    id: int
    name: str
    iso_code: str
    continent: Optional[str] = None
    flag_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CompetitionResponse(BaseModel):
    id: int
    name: str
    type: CompetitionType
    country_id: Optional[int] = None
    continent: Optional[str] = None
    logo_url: Optional[str] = None
    strength_embedding: Optional[List[float]] = None

    model_config = ConfigDict(from_attributes=True)


class TeamResponse(BaseModel):
    id: int
    name: str
    country_id: int
    is_national_team: bool
    current_competition_id: Optional[int] = None
    logo_url: Optional[str] = None
    fotmob_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PlayerResponse(BaseModel):
    id: int
    name: str
    birth_date: Optional[date] = None
    nationality_id: int
    current_team_id: Optional[int] = None
    image_url: Optional[str] = None
    fotmob_id: Optional[int] = None
    position_group: PositionGroup
    specific_positions: List[str] = Field(default_factory=list)
    height_cm: Optional[int] = None
    preferred_foot: Optional[str] = None
    contract_expiry: Optional[date] = None
    ability_vector: Optional[List[float]] = None
    current_gem_score: Optional[float] = None
    current_market_value: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Create / ingestion schemas (match DB columns)
# ==========================================

class PlayerSeasonStatCreate(BaseModel):
    player_id: int
    team_id: int
    competition_id: int
    season_id: str

    minutes: int
    goals: int = 0
    assists: int = 0
    xg: Optional[float] = None
    xa: Optional[float] = None
    rating: Optional[float] = None
    yellow_cards: int = 0
    red_cards: int = 0

    detailed_stats: Dict[str, Any] = Field(default_factory=dict)


class MatchSnapshotCreate(BaseModel):
    player_id: int
    date: date
    opponent_id: int
    competition_id: int
    minutes_played: int
    match_rating: Optional[float] = None
    stats: Dict[str, Any] = Field(default_factory=dict)


class TransferCreate(BaseModel):
    player_id: int
    date: date
    from_team_id: int
    to_team_id: int
    fee_amount: float
    currency: str = "EUR"


class TeamMatchResultCreate(BaseModel):
    date: date
    team_id: int
    opponent_id: int
    competition_id: int
    season_id: str

    goals_for: int
    goals_against: int
    is_home: bool = True
    is_neutral_venue: bool = False

    xg_for: Optional[float] = None
    xg_against: Optional[float] = None
    possession: Optional[float] = None


class PlayerInternationalStatCreate(BaseModel):
    player_id: int
    level: InternationalLevel
    country_id: int
    caps: int = 0
    goals: int = 0
    years_active: Optional[str] = None


class ValuationPredictionCreate(BaseModel):
    player_id: int
    date: Optional[date] = None
    predicted_value: float
    model_version: Optional[str] = None


# ==========================================
# Scraper / master input bag (keeps friendly fields)
# Uses DB-aligned enums but keeps names useful for scraping
# ==========================================

class PlayerScraperInput(BaseModel):
    name: str
    nationality_name: Optional[str] = None
    birth_date: Optional[date] = None

    height_cm: Optional[int] = None
    preferred_foot: Optional[str] = None
    image_url: Optional[str] = None
    contract_expiry: Optional[date] = None
    current_market_value: Optional[float] = None

    fotmob_id: Optional[int] = None
    transfermarkt_id: Optional[str] = None

    position_group: PositionGroup
    specific_positions: List[str] = Field(default_factory=list)

    season_stats: List[PlayerSeasonStatCreate] = Field(default_factory=list)
    recent_matches: List[MatchSnapshotCreate] = Field(default_factory=list)
    transfer_history: List[TransferCreate] = Field(default_factory=list)
