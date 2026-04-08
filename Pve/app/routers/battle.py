"""Battle outcome and hero level-up endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.db_models import Campaign, CampaignHero, RoomEvent, CampaignStatus
from app.models.db_models import RoomType as DBRoomType
from app.models.schemas import (
    BattleResultIn, BattleResultOut, LevelUpRequest, LevelUpResponse,
)
from app.services.battle_service import process_battle_result
from app.services.hero_service import try_level_up, hero_to_schema
from app.services.constants import exp_needed_for_level

router = APIRouter(prefix="/campaign", tags=["battle"])


@router.post("/{campaign_id}/battle-result", response_model=BattleResultOut)
def submit_battle_result(
    campaign_id: int,
    body: BattleResultIn,
    db: Session = Depends(get_db),
):
    """
    Called by the Battle Service (or client) after a battle concludes.
    Distributes XP/gold on win, applies penalties on loss.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    if campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Campaign is not active.")

    # Validate a battle room is indeed pending
    pending = (
        db.query(RoomEvent)
        .filter(
            RoomEvent.campaign_id == campaign_id,
            RoomEvent.room_type == DBRoomType.BATTLE,
            RoomEvent.completed == False,
        )
        .first()
    )
    if not pending:
        raise HTTPException(status_code=409, detail="No pending battle room found.")

    if body.result not in ("win", "loss"):
        raise HTTPException(status_code=422, detail="result must be 'win' or 'loss'.")

    return process_battle_result(
        campaign=campaign,
        result=body.result,
        surviving_hero_ids=body.surviving_hero_ids,
        enemy_units=body.enemy_party,
        db=db,
    )


@router.post("/{campaign_id}/hero/{hero_id}/level-up", response_model=LevelUpResponse)
def level_up_hero(
    campaign_id: int,
    hero_id: int,
    body: LevelUpRequest,
    db: Session = Depends(get_db),
):
    """Level up a hero in the specified class (if they have enough XP)."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    hero = (
        db.query(CampaignHero)
        .filter(CampaignHero.id == hero_id, CampaignHero.campaign_id == campaign_id)
        .first()
    )
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found in this campaign.")

    did_level_up, message = try_level_up(hero, body.class_to_level.value, db)
    exp_needed = exp_needed_for_level(hero.level + 1) if hero.level < 20 else 0

    return LevelUpResponse(
        hero=hero_to_schema(hero),
        levelled_up=did_level_up,
        message=message,
        exp_needed=exp_needed,
        exp_current=hero.experience,
    )
