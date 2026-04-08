import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Fallback to SQLite only for local testing without Docker
DEFAULT_DB_URL = "sqlite:///./pvp_service.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Use 'check_same_thread' ONLY for SQLite
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
    # Make sure to import all models so Base knows they exist
    from infrastructure.models.user_model import UserModel
    from infrastructure.models.party_model import PartyModel
    from infrastructure.models.league_record_model import LeagueRecordModel
    
    Base.metadata.create_all(bind=engine)