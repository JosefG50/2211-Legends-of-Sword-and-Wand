"""Process battle outcomes: XP, gold, penalties, return to inn on loss."""
from sqlalchemy.orm import Session
from app.models.db_models import Campaign, CampaignHero, RoomEvent
from app.models.schemas import BattleResultIn, BattleResultOut, EnemyUnit
from app.services.hero_service import hero_to_schema
from app.services.constants import exp_needed_for_level
from app.config import settings
import logging
import math

logger = logging.getLogger(__name__)


def _exp_for_enemy(level: int) -> int:
    return settings.EXP_PER_LEVEL * level


def _gold_for_enemy(level: int) -> int:
    return settings.GOLD_PER_LEVEL * level


def process_battle_result(
    campaign: Campaign,
    result: str,
    surviving_hero_ids: list[int],
    enemy_units: list[EnemyUnit],
    db: Session,
) -> BattleResultOut:
    """
    Apply win/loss consequences to the campaign.

    Win:
      - Award EXP and gold split among surviving heroes
      - Mark dead heroes (those not in surviving_hero_ids)

    Loss:
      - Deduct 10% gold
      - Deduct 30% current-level EXP from each hero (no level loss)
      - Return to last inn room
    """
    heroes: list[CampaignHero] = campaign.heroes

    # Mark current room as completed
    room_event = (
        db.query(RoomEvent)
        .filter(
            RoomEvent.campaign_id == campaign.id,
            RoomEvent.room_number == campaign.current_room,
            RoomEvent.completed == False,
        )
        .first()
    )
    if room_event:
        room_event.completed = True
        room_event.result = result

    gold_change = 0
    exp_change = 0
    message = ""

    if result == "win":
        # Calculate totals
        total_exp = sum(_exp_for_enemy(e.level) for e in enemy_units)
        total_gold = sum(_gold_for_enemy(e.level) for e in enemy_units)

        # Mark fallen heroes
        surviving_set = set(surviving_hero_ids)
        for hero in heroes:
            if hero.id not in surviving_set:
                hero.is_alive = False
                hero.hp = 0

        # Split XP among survivors
        survivors = [h for h in heroes if h.id in surviving_set]
        if survivors:
            exp_per_hero = total_exp // len(survivors)
            for hero in survivors:
                hero.experience += exp_per_hero

        campaign.gold += total_gold
        gold_change = total_gold
        exp_change = total_exp
        message = (
            f"Victory! Gained {total_exp} EXP and {total_gold} gold. "
            f"{len(survivors)}/{len(heroes)} heroes survived."
        )
        logger.info(f"Campaign {campaign.id} won battle. +{total_gold}g +{total_exp}exp")

    else:  # loss
        # Deduct 10% gold
        gold_penalty = math.ceil(campaign.gold * settings.LOSS_GOLD_PENALTY)
        campaign.gold = max(0, campaign.gold - gold_penalty)
        gold_change = -gold_penalty

        # Deduct 30% current-level EXP from each hero (floor at 0)
        total_exp_lost = 0
        for hero in heroes:
            exp_penalty = math.ceil(hero.experience * settings.LOSS_EXP_PENALTY)
            hero.experience = max(0, hero.experience - exp_penalty)
            total_exp_lost += exp_penalty
        exp_change = -total_exp_lost

        # Return to last inn room
        campaign.current_room = campaign.last_inn_room

        message = (
            f"Defeat! Lost {gold_penalty} gold and {total_exp_lost} EXP. "
            f"Returned to room {campaign.last_inn_room}."
        )
        logger.info(f"Campaign {campaign.id} lost battle. Returned to room {campaign.last_inn_room}")

    db.commit()

    return BattleResultOut(
        campaign_id=campaign.id,
        result=result,
        gold_change=gold_change,
        exp_change=exp_change,
        new_gold=campaign.gold,
        heroes=[hero_to_schema(h) for h in heroes],
        message=message,
        room_number=campaign.current_room,
    )
