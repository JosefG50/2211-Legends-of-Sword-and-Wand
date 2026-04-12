from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


# ---------- Enums ----------

class RoomType(str, Enum):
    BATTLE = "battle"
    INN = "inn"


class HeroClass(str, Enum):
    ORDER = "order"
    CHAOS = "chaos"
    WARRIOR = "warrior"
    MAGE = "mage"
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


class CampaignStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# ---------- Hero ----------

class HeroBase(BaseModel):
    name: str
    hero_class: HeroClass


class HeroCreate(HeroBase):
    pass


class HeroStats(BaseModel):
    id: int
    name: str
    hero_class: HeroClass
    level: int
    experience: int
    attack: int
    defense: int
    hp: int
    max_hp: int
    mana: int
    max_mana: int
    is_alive: bool
    is_stunned: bool
    class_levels: Dict[str, int] = {}
    specialization: Optional[HeroClass] = None
    is_hybrid: bool

    class Config:
        from_attributes = True


# ---------- Campaign ----------

class CampaignCreate(BaseModel):
    user_id: int
    username: str
    hero_name: str
    hero_class: HeroClass


class CampaignSummary(BaseModel):
    id: int
    status: CampaignStatus
    current_room: int
    gold: int

    class Config:
        from_attributes = True


class CampaignState(BaseModel):
    id: int
    user_id: int
    status: CampaignStatus
    current_room: int
    gold: int
    last_inn_room: int
    heroes: List[HeroStats]

    class Config:
        from_attributes = True


# ---------- Room ----------

class RoomResult(BaseModel):
    campaign_id: int
    room_number: int
    room_type: RoomType
    battle_chance: float
    enemy_party: Optional[List["EnemyUnit"]] = None
    inn_data: Optional["InnData"] = None


# ---------- Enemy ----------

class EnemyUnit(BaseModel):
    id: int
    level: int
    attack: int
    defense: int
    hp: int
    max_hp: int
    is_alive: bool = True
    is_stunned: bool = False


class EnemyParty(BaseModel):
    units: List[EnemyUnit]
    cumulative_level: int


# ---------- Battle Result ----------

class BattleResultIn(BaseModel):
    campaign_id: int
    result: str  # "win" | "loss"
    surviving_hero_ids: List[int]
    enemy_party: List[EnemyUnit]


class BattleResultOut(BaseModel):
    campaign_id: int
    result: str
    gold_change: int
    exp_change: int
    new_gold: int
    heroes: List[HeroStats]
    message: str
    room_number: int


# ---------- Inn ----------

class InnItem(BaseModel):
    name: str
    cost: int
    effect: str
    hp_effect: int = 0
    mana_effect: int = 0
    is_revive: bool = False


class InnHero(BaseModel):
    id: str  # temporary ID for the recruitment pool
    name: str
    hero_class: HeroClass
    level: int
    recruit_cost: int


class InnData(BaseModel):
    revived_heroes: List[str]
    healed_heroes: Dict[str, int]   # hero_name -> hp restored
    mana_restored: Dict[str, int]   # hero_name -> mana restored
    available_items: List[InnItem]
    available_heroes: List[InnHero]
    party_full: bool


class PurchaseRequest(BaseModel):
    item_name: str
    quantity: int = 1


class PurchaseResponse(BaseModel):
    success: bool
    message: str
    gold_remaining: int
    item_name: str
    quantity: int


class RecruitRequest(BaseModel):
    hero_pool_id: str
    hero_name: str


class RecruitResponse(BaseModel):
    success: bool
    message: str
    gold_remaining: int
    hero: Optional[HeroStats] = None


# ---------- Level Up ----------

class LevelUpRequest(BaseModel):
    hero_id: int
    class_to_level: HeroClass


class LevelUpResponse(BaseModel):
    hero: HeroStats
    levelled_up: bool
    message: str
    exp_needed: int
    exp_current: int


# ---------- Score ----------

class ScoreResponse(BaseModel):
    campaign_id: int
    user_id: int
    username: str
    total_score: int
    hero_level_score: int
    gold_score: int
    item_score: int
    rank: int


class HallOfFameEntry(BaseModel):
    rank: int
    username: str
    total_score: int
    campaign_id: int


class HallOfFame(BaseModel):
    entries: List[HallOfFameEntry]


# ---------- Save/Resume ----------

class SaveResponse(BaseModel):
    success: bool
    message: str
    campaign_id: int


class SavePartyRequest(BaseModel):
    campaign_id: int
    user_id: int
    replace_party_id: Optional[int] = None


class SavePartyResponse(BaseModel):
    success: bool
    message: str
    saved_party_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserOut
    created: bool


RoomResult.model_rebuild()
