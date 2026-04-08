"""Map / campaign progression logic."""
import random
from sqlalchemy.orm import Session
from app.models.db_models import Campaign, CampaignHero, RoomEvent, CampaignStatus
from app.models.db_models import RoomType as DBRoomType
from app.models.schemas import RoomResult, RoomType, EnemyUnit, InnData
from app.services.constants import (
    enemy_attack, enemy_defense, enemy_hp, RANDOM_HERO_NAMES,
)
from app.services.inn_service import build_inn_data
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def compute_battle_chance(cumulative_hero_level: int) -> float:
    """
    Base 60% battle chance, +3% per 10 cumulative hero levels.
    Capped at MAX_BATTLE_CHANCE.
    """
    shifts = cumulative_hero_level // 10
    chance = settings.BASE_BATTLE_CHANCE + shifts * settings.CHANCE_SHIFT_PER_10_LEVELS
    return min(chance, settings.MAX_BATTLE_CHANCE)


def generate_enemy_party(player_cumulative_level: int) -> list[EnemyUnit]:
    """
    Generate a random enemy party scaled to the player's cumulative level.
    - 1-5 units
    - Enemy cumulative level in range [max(1, pcl-10), pcl]
    - Each unit level 1-10
    """
    num_units = random.randint(1, 5)

    # Target cumulative level window
    low = max(num_units, player_cumulative_level - 10)
    high = max(num_units, player_cumulative_level)

    # Distribute target cumulative level across units
    target_total = random.randint(low, high)

    # Assign levels: random split, each at least 1
    levels: list[int] = []
    remaining = target_total
    for i in range(num_units - 1):
        max_for_this = min(10, remaining - (num_units - i - 1))
        lvl = random.randint(1, max(1, max_for_this))
        levels.append(lvl)
        remaining -= lvl
    levels.append(max(1, min(10, remaining)))

    units = []
    for i, lvl in enumerate(levels):
        hp = enemy_hp(lvl)
        units.append(EnemyUnit(
            id=i + 1,
            level=lvl,
            attack=enemy_attack(lvl),
            defense=enemy_defense(lvl),
            hp=hp,
            max_hp=hp,
        ))
    return units


def advance_room(campaign: Campaign, db: Session) -> RoomResult:
    """
    Move the campaign to the next room and determine its type.
    Returns a RoomResult with either enemy party or inn data.
    """
    campaign.current_room += 1
    db.flush()

    heroes = [h for h in campaign.heroes if h.is_alive]
    cumulative_level = sum(h.level for h in campaign.heroes)
    battle_chance = compute_battle_chance(cumulative_level)

    roll = random.random()
    room_type = RoomType.BATTLE if roll < battle_chance else RoomType.INN

    # Persist the room event
    room_event = RoomEvent(
        campaign_id=campaign.id,
        room_number=campaign.current_room,
        room_type=DBRoomType(room_type.value),
        completed=False,
    )
    db.add(room_event)

    result = RoomResult(
        campaign_id=campaign.id,
        room_number=campaign.current_room,
        room_type=room_type,
        battle_chance=battle_chance,
    )

    if room_type == RoomType.BATTLE:
        enemy_party = generate_enemy_party(cumulative_level)
        room_event.enemy_party_snapshot = [e.model_dump() for e in enemy_party]
        result.enemy_party = enemy_party
    else:
        # Inn: update last_inn_room, heal party, build inn data
        campaign.last_inn_room = campaign.current_room
        inn_data = build_inn_data(campaign, db)
        result.inn_data = inn_data

    db.commit()
    return result


def get_current_room_event(campaign_id: int, db: Session) -> RoomEvent | None:
    return (
        db.query(RoomEvent)
        .filter(
            RoomEvent.campaign_id == campaign_id,
            RoomEvent.completed == False,
        )
        .order_by(RoomEvent.room_number.desc())
        .first()
    )
