from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey,
    DateTime, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class RoomType(str, enum.Enum):
    BATTLE = "battle"
    INN = "inn"


class CampaignStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.ACTIVE, nullable=False)
    current_room = Column(Integer, default=0, nullable=False)
    gold = Column(Integer, default=0, nullable=False)
    last_inn_room = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    heroes = relationship("CampaignHero", back_populates="campaign", cascade="all, delete-orphan")
    rooms = relationship("RoomEvent", back_populates="campaign", cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="campaign", cascade="all, delete-orphan")
    score = relationship("Score", back_populates="campaign", uselist=False, cascade="all, delete-orphan")


class HeroClass(str, enum.Enum):
    ORDER = "order"
    CHAOS = "chaos"
    WARRIOR = "warrior"
    MAGE = "mage"
    # Hybrid classes
    PRIEST = "priest"
    HERETIC = "heretic"
    PALADIN = "paladin"
    PROPHET = "prophet"
    INVOKER = "invoker"
    ROGUE = "rogue"
    SORCERER = "sorcerer"
    KNIGHT = "knight"
    WARLOCK = "warlock"
    WIZARD = "wizard"


class CampaignHero(Base):
    __tablename__ = "campaign_heroes"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String(100), nullable=False)
    hero_class = Column(SAEnum(HeroClass), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    experience = Column(Integer, default=0, nullable=False)
    attack = Column(Integer, default=5, nullable=False)
    defense = Column(Integer, default=5, nullable=False)
    hp = Column(Integer, default=100, nullable=False)
    max_hp = Column(Integer, default=100, nullable=False)
    mana = Column(Integer, default=50, nullable=False)
    max_mana = Column(Integer, default=50, nullable=False)
    is_alive = Column(Boolean, default=True, nullable=False)
    is_stunned = Column(Boolean, default=False, nullable=False)
    # Track class levels for hybrid system
    class_levels = Column(JSON, default=dict)  # {"order": 2, "warrior": 3}
    specialization = Column(SAEnum(HeroClass), nullable=True)
    is_hybrid = Column(Boolean, default=False, nullable=False)

    campaign = relationship("Campaign", back_populates="heroes")


class RoomEvent(Base):
    __tablename__ = "room_events"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    room_number = Column(Integer, nullable=False)
    room_type = Column(SAEnum(RoomType), nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    enemy_party_snapshot = Column(JSON, nullable=True)   # Snapshot of generated enemies
    result = Column(String(10), nullable=True)            # "win" | "loss"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign", back_populates="rooms")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    item_name = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    purchase_price = Column(Integer, nullable=False)

    campaign = relationship("Campaign", back_populates="inventory")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, unique=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    total_score = Column(Integer, nullable=False)
    hero_level_score = Column(Integer, nullable=False)
    gold_score = Column(Integer, nullable=False)
    item_score = Column(Integer, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign", back_populates="score")
