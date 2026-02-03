import logging
from sqlalchemy.orm import Session
from src.database.db import SessionLocal
from src.database.models import Country, Competition, Team, CompetitionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_or_create_country(db: Session, name: str, iso: str, flag: str):
    """Helper function to avoid repeating code"""
    country = db.query(Country).filter_by(name=name).first()
    if not country:
        country = Country(name=name, iso_code=iso, continent="Europe", flag_url=flag)
        db.add(country)
        db.commit()
        db.refresh(country)
        logger.info(f"✅ Created Country: {name}")
    return country

def get_or_create_league(db: Session, name: str, country_id: int, logo: str):
    """Helper function for Leagues"""
    league = db.query(Competition).filter_by(name=name).first()
    if not league:
        league = Competition(
            name=name, type=CompetitionType.LEAGUE, country_id=country_id,
            continent="Europe", logo_url=logo
        )
        db.add(league)
        db.commit()
        db.refresh(league)
        logger.info(f"✅ Created League: {name}")
    return league

def seed_england(db: Session):
    logger.info("--- Seeding England ---")
    england = get_or_create_country(
        db, "England", "ENG", 
        "https://upload.wikimedia.org/wikipedia/en/b/be/Flag_of_England.svg"
    )
    
    prem = get_or_create_league(
        db, "Premier League", england.id,
        logo="https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg"
    )

    teams = [
        "AFC Bournemouth", "Arsenal", "Aston Villa", "Brentford", "Brighton & Hove Albion",
        "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham", "Leeds United",
        "Liverpool", "Manchester City", "Manchester United", "Newcastle United",
        "Nottingham Forest", "Sunderland", "Tottenham Hotspur",
        "West Ham United", "Wolverhampton Wanderers"
    ]
    
    # Bulk insert logic could go here, but loop is fine for 20 items
    for name in teams:
        if not db.query(Team).filter_by(name=name).first():
            db.add(Team(name=name, country_id=england.id, current_competition_id=prem.id))
            logger.info(f"   + Added {name}")
    db.commit()

def seed_static_data():
    db: Session = SessionLocal()
    try:
        seed_england(db)
        # seed_spain(db) # Uncomment when ready
        # seed_germany(db)
    except Exception as e:
        logger.error(f"❌ Seeding Failed: {e}")
        db.rollback()
    finally:
        db.close()
        logger.info("🏁 Static Seeding Finished.")

if __name__ == "__main__":
    seed_static_data()