from datetime import date, datetime
from typing import List, Optional
from uuid import UUID, uuid4
import enum

from sqlalchemy import (
    String, Integer, Float, Boolean, Date, DateTime, 
    ForeignKey, UniqueConstraint, Index, Enum, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .db import Base

class CompetitionType(str, enum.Enum):
    LEAGUE = "league"
    DOMESTIC_CUP = "domestic_cup"
    CONTINENTAL = "continental"   # UCL, Libertadores
    INTERNATIONAL = "international" # World Cup, Euros

class PositionGroup(str, enum.Enum):
    """
    Refined categories for ML partitioning.
    Aligns with FotMob/FBref comparisons for fairer 'Gem Scores'.
    """
    GOALKEEPER = "Goalkeeper"
    CENTRE_BACK = "Centre-Back"        # CB
    FULL_BACK = "Full-Back"            # LB, RB, LWB, RWB
    MIDFIELDER = "Midfielder"          # CDM, CM 
    WINGER_AM = "Winger_AM"            # LW, RW, CAM, #10s 
    STRIKER = "Striker"                # CF, ST 

class InternationalLevel(enum.Enum):
    SENIOR = "Senior"
    U23 = "U23" # Olympic
    U21 = "U21"
    U20 = "U20"
    U19 = "U19"
    U18 = "U18"
    U17 = "U17"
    U16 = "U16"
    U15 = "U15"

class Country(Base):
    __tablename__ = "countries"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    iso_code: Mapped[str] = mapped_column(String(3)) 
    continent: Mapped[str] = mapped_column(String(20))

    flag_url: Mapped[Optional[str]] = mapped_column(String(255)) # New
    
    competitions: Mapped[List["Competition"]] = relationship(back_populates="country")
    teams: Mapped[List["Team"]] = relationship(back_populates="country")
    players: Mapped[List["Player"]] = relationship(back_populates="nationality_country")


class RankingSnapshot(Base):
    """Tracks historical coefficients/rankings over time."""
    __tablename__ = "ranking_snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20)) # "Country", "League"
    entity_id: Mapped[int] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date)
    points: Mapped[float] = mapped_column(Float)

class Competition(Base):
    __tablename__ = "competitions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[CompetitionType] = mapped_column(Enum(CompetitionType))

    logo_url: Mapped[Optional[str]] = mapped_column(String(255)) # New
    
    country_id: Mapped[Optional[int]] = mapped_column(ForeignKey("countries.id"))
    continent: Mapped[Optional[str]] = mapped_column(String(20))
    
    # ML: Learned difficulty vector
    strength_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(8))
    
    country: Mapped["Country"] = relationship(back_populates="competitions")
    team_history: Mapped[List["TeamSeasonContext"]] = relationship(back_populates="competition")

class Team(Base):
    __tablename__ = "teams"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    is_national_team: Mapped[bool] = mapped_column(Boolean, default=False)
    current_competition_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competitions.id"))

    logo_url: Mapped[Optional[str]] = mapped_column(String(255)) # New
    fotmob_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    
    country: Mapped["Country"] = relationship(back_populates="teams")
    season_history: Mapped[List["TeamSeasonContext"]] = relationship(back_populates="team")
    players: Mapped[List["PlayerSeasonStat"]] = relationship(back_populates="team")
    current_competition: Mapped["Competition"] = relationship(foreign_keys=[current_competition_id])

class TeamSeasonContext(Base):
    """Tracks which league a team was in for a specific season."""
    __tablename__ = "team_season_context"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[str] = mapped_column(String(20)) # "2024-2025"

    final_position: Mapped[Optional[int]] = mapped_column(Integer) # e.g. 1st, 18th
    points: Mapped[Optional[int]] = mapped_column(Integer) # e.g. 94 points
    goals_for: Mapped[Optional[int]] = mapped_column(Integer) # e.g. 102 goals
    goals_against: Mapped[Optional[int]] = mapped_column(Integer) # e.g. 34 goals
    
    team: Mapped["Team"] = relationship(back_populates="season_history")
    competition: Mapped["Competition"] = relationship(back_populates="team_history")

class Player(Base):
    __tablename__ = "players"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_date: Mapped[date] = mapped_column(Date)
    nationality_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    current_team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"))

    image_url: Mapped[Optional[str]] = mapped_column(String(255)) # New
    fotmob_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    position_group: Mapped[PositionGroup] = mapped_column(Enum(PositionGroup))
    specific_positions: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])

    height_cm: Mapped[Optional[int]] = mapped_column(Integer) 
    preferred_foot: Mapped[Optional[str]] = mapped_column(String(10)) # "left", "right"
    contract_expiry: Mapped[Optional[date]] = mapped_column(Date)
    
    # ML: The core quality vector
    ability_vector: Mapped[Optional[List[float]]] = mapped_column(Vector(64))
    
    # Live Dashboard Data
    current_gem_score: Mapped[Optional[float]] = mapped_column(Float)
    current_market_value: Mapped[Optional[float]] = mapped_column(Float)
    
    nationality_country: Mapped["Country"] = relationship(back_populates="players")
    stats: Mapped[List["PlayerSeasonStat"]] = relationship(back_populates="player")
    transfers: Mapped[List["Transfer"]] = relationship(back_populates="player")
    current_team: Mapped["Team"] = relationship(foreign_keys=[current_team_id])
    international_stats: Mapped[List["PlayerInternationalStat"]] = relationship(back_populates="player")

    __table_args__ = (
        # 1. Hard constraint: No two players can share the same FotMob ID
        UniqueConstraint('fotmob_id', name='_fotmob_player_uc'),
        # 2. Index for fast lookup by
        Index('idx_player_lookup', 'name', 'nationality_id'),
    )

class PlayerSeasonStat(Base):
    """Aggregated Season Data (Macro View)"""
    __tablename__ = "player_season_stats"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[str] = mapped_column(String(20))
    
    minutes: Mapped[int] = mapped_column(Integer)
    goals: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)

    # "Moneyball" stats that are critical enough to be columns
    xg: Mapped[Optional[float]] = mapped_column(Float) # Expected Goals
    xa: Mapped[Optional[float]] = mapped_column(Float) # Expected Assists
    rating: Mapped[Optional[float]] = mapped_column(Float) # Average Match Rating
    
    # Discipline is common enough to keep explicit
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, default=0)
    
    # Flexible storage for advanced metrics (xG, pressures, etc.)
    detailed_stats: Mapped[dict] = mapped_column(JSONB, default={})
    
    player: Mapped["Player"] = relationship(back_populates="stats")
    team: Mapped["Team"] = relationship(back_populates="players")

    __table_args__ = (
        # Ensure a player has only ONE stats row per Team+Competition+Season
        UniqueConstraint('player_id', 'team_id', 'competition_id', 'season_id', name='_player_season_stat_uc'),
        
        # Speed up the "Show me Player X's history" query
        Index('idx_player_history', 'player_id', 'season_id'),
    )


class Transfer(Base):
    __tablename__ = "transfers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    from_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    to_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    
    date: Mapped[date] = mapped_column(Date)
    fee_amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    
    player: Mapped["Player"] = relationship(back_populates="transfers")

class ValuationPrediction(Base):
    """Log of what our model predicted vs reality"""
    __tablename__ = "valuation_predictions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    date: Mapped[date] = mapped_column(Date, default=datetime.now)
    predicted_value: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(20))



class MatchSnapshot(Base):
    """
    Individual Match Data (Micro View).
    Crucial for: Form calculation, Debut tracking, Wonderkid Radar.
    """
    __tablename__ = "match_snapshots"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    
    date: Mapped[date] = mapped_column(Date)
    opponent_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    
    minutes_played: Mapped[int] = mapped_column(Integer)
    match_rating: Mapped[float] = mapped_column(Float, nullable=True) # e.g. 7.4
    
    # Store raw stats for this single game (goals, xG, etc.)
    stats: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Relationships
    player: Mapped["Player"] = relationship()
    opponent: Mapped["Team"] = relationship(foreign_keys=[opponent_id])

class TeamMatchResult(Base):
    """
    The 'Anchor' Data.
    Used to train League Embeddings and ELO ratings.
    Tracks: "Did Team A dominate Team B?" (Scoreline + Stats)
    """
    __tablename__ = "team_match_results"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    
    # Who Played?
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    opponent_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[str] = mapped_column(String(20))
    
    # The Result
    goals_for: Mapped[int] = mapped_column(Integer)
    goals_against: Mapped[int] = mapped_column(Integer)
    is_home: Mapped[bool] = mapped_column(Boolean, default=True)
    is_neutral_venue: Mapped[bool] = mapped_column(Boolean, default=False) # Important for Finals
    
    # The "Dominance" Metrics (Used for Weighting)
    # If City wins 1-0 but has 3.5 xG vs 0.1 xG, the model learns MORE.
    xg_for: Mapped[Optional[float]] = mapped_column(Float)
    xg_against: Mapped[Optional[float]] = mapped_column(Float)
    possession: Mapped[Optional[float]] = mapped_column(Float) # 0.0 to 1.0
    
    team: Mapped["Team"] = relationship(foreign_keys=[team_id])
    opponent: Mapped["Team"] = relationship(foreign_keys=[opponent_id])
    competition: Mapped["Competition"] = relationship()

    __table_args__ = (
        # 1. Sanity Check: Team cannot play opponent with same ID
        CheckConstraint('team_id != opponent_id', name='check_team_vs_opponent'),
        
        # 2. No Duplicates: A team can't have two results vs same opponent on same day
        UniqueConstraint('team_id', 'opponent_id', 'date', name='_team_match_result_uc'),
    )


class PlayerInternationalStat(Base):
    """
    Summary Stats for International Career.
    Separated from SeasonStats because international 'seasons' are age-bound.
    """
    __tablename__ = "player_international_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)  
    level: Mapped[InternationalLevel] = mapped_column(Enum(InternationalLevel), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)

    caps: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)

    years_active: Mapped[Optional[str]] = mapped_column(String(20))

    player: Mapped["Player"] = relationship(back_populates="international_stats")
    country: Mapped["Country"] = relationship()

    # Constraint: A player can only have ONE summary row per level per country
    __table_args__ = (
        UniqueConstraint('player_id', 'level', 'country_id', name='_player_level_country_uc'),
    )