import os
from dotenv import load_dotenv # New import
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1. Load the secrets from the .env file
load_dotenv()

# 2. Construct the URL securely
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
dbname = os.getenv("POSTGRES_DB")

# Default to localhost if not specified
DATABASE_URL = f"postgresql://{user}:{password}@localhost:5432/{dbname}"

# ... rest of the file remains the same ...
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()