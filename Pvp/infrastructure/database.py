import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The URL is pulled from docker-compose (Postgres)
DEFAULT_DB_URL = "sqlite:///./pvp_service.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def init_db():
    # We only import the LeagueRecordModel here.
    # We do NOT import UserModel or PartyModel because 
    # PvE owns those tables. PvP will just "read" them.
    from infrastructure.models.league_record_model import LeagueRecordModel
    
    # This will only create the league_records table if it doesn't exist.
    Base.metadata.create_all(bind=engine)