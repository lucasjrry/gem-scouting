import logging
from sqlalchemy import text

# 1. Import the engine and Base from YOUR existing db.py
from src.database.db import engine, Base

# 2. Import ALL your models. 
# SQLAlchemy needs to "see" them to create the tables.
# (If you don't import them here, the tables won't be created)
from src.database.models import (
    Country, 
    Competition, 
    Team, 
    Player, 
    PlayerSeasonStat, 
    PlayerInternationalStat, 
    MatchSnapshot, 
    TeamMatchResult, 
    Transfer,
    ValuationPrediction,
    TeamSeasonContext,
    RankingSnapshot
)

# Set up logging so you can see the SQL commands in the terminal
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def init_db():
    print("🚀 Connecting to database...")
    
    with engine.connect() as connection:
        print("🔌 Enabling pgvector extension...")
        # This is required for the 'ability_vector' column to work
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()
        
    print("🏗️  Creating Tables...")
    # This looks at all the imported models and generates the "CREATE TABLE" SQL
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_db()