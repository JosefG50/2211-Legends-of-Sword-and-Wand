"""Shared pytest fixtures for the PvE service test suite."""
import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.db.session import get_db
from app.models.db_models import Base, Campaign, CampaignHero, HeroClass, CampaignStatus

# ---------- In-memory SQLite engine ----------
TEST_DATABASE_URL = "sqlite:///./test_pve.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Session:
    """Provide a transactional test DB session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """FastAPI test client wired to the test DB session."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------- Helper factories ----------

def make_campaign(db: Session, user_id: int = 1, gold: int = 500, room: int = 0) -> Campaign:
    c = Campaign(
        user_id=user_id,
        status=CampaignStatus.ACTIVE,
        current_room=room,
        gold=gold,
        last_inn_room=0,
    )
    db.add(c)
    db.flush()
    return c


def make_hero(
    db: Session,
    campaign_id: int,
    name: str = "Aldric",
    hero_class: str = "warrior",
    level: int = 1,
    hp: int = 100,
    mana: int = 50,
    experience: int = 0,
    is_alive: bool = True,
) -> CampaignHero:
    hero = CampaignHero(
        campaign_id=campaign_id,
        name=name,
        hero_class=HeroClass(hero_class),
        level=level,
        experience=experience,
        attack=5 + (level - 1) * 3,
        defense=5 + (level - 1) * 2,
        hp=hp,
        max_hp=100 + (level - 1) * 10,
        mana=mana,
        max_mana=50 + (level - 1) * 5,
        is_alive=is_alive,
        is_stunned=False,
        class_levels={hero_class: level},
    )
    db.add(hero)
    db.flush()
    return hero


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Session:
    """Provide a transactional test DB session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """FastAPI test client wired to the test DB session."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------- Helper factories ----------

def make_campaign(db: Session, user_id: int = 1, gold: int = 500, room: int = 0) -> Campaign:
    c = Campaign(
        user_id=user_id,
        status=CampaignStatus.ACTIVE,
        current_room=room,
        gold=gold,
        last_inn_room=0,
    )
    db.add(c)
    db.flush()
    return c


def make_hero(
    db: Session,
    campaign_id: int,
    name: str = "Aldric",
    hero_class: str = "warrior",
    level: int = 1,
    hp: int = 100,
    mana: int = 50,
    experience: int = 0,
    is_alive: bool = True,
) -> CampaignHero:
    hero = CampaignHero(
        campaign_id=campaign_id,
        name=name,
        hero_class=HeroClass(hero_class),
        level=level,
        experience=experience,
        attack=5 + (level - 1) * 3,
        defense=5 + (level - 1) * 2,
        hp=hp,
        max_hp=100 + (level - 1) * 10,
        mana=mana,
        max_mana=50 + (level - 1) * 5,
        is_alive=is_alive,
        is_stunned=False,
        class_levels={hero_class: level},
    )
    db.add(hero)
    db.flush()
    return hero
