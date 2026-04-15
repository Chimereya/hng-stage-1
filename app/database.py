import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=5,             # Maintain up to 5 permanent connections
    max_overflow=10,         # Allow 10 extra temporary connections
    pool_timeout=30,         # Wait 30s for a connection before failing
    pool_recycle=1800,       # Close and reopen connections every 30 mins
    pool_pre_ping=True,      # Checks if connection is alive before every query
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() # Base class for models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()