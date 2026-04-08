"""Inn endpoints: item shop and hero recruitment."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.db_models import Campaign, CampaignStatus, RoomEvent
from app.models.db_models import RoomType as DBRoomType
from app.models.schemas import (
    PurchaseRequest, PurchaseResponse,
    RecruitRequest, RecruitResponse,
    InnData, InnHero,
)
from app.services.inn_service import purchase_item, recruit_hero, build_inn_data
from app.services.constants import INN_ITEMS
import json

router = APIRouter(prefix="/campaign", tags=["inn"])

# In-memory inn hero pool cache keyed by campaign_id
# In production this would be stored in Redis or the DB
_INN_HERO_CACHE: dict[int, list[InnHero]] = {}


def _get_active_inn_room(campaign_id: int, db: Session) -> RoomEvent:
    event = (
        db.query(RoomEvent)
        .filter(
            RoomEvent.campaign_id == campaign_id,
            RoomEvent.room_type == DBRoomType.INN,
            RoomEvent.completed == False,
        )
        .order_by(RoomEvent.room_number.desc())
        .first()
    )
    if not event:
        raise HTTPException(
            status_code=409,
            detail="No active inn room. Navigate to an inn first.",
        )
    return event


@router.get("/{campaign_id}/inn", response_model=InnData)
def get_inn(campaign_id: int, db: Session = Depends(get_db)):
    """Get the current inn state: healing results, shop items, recruitable heroes."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    _get_active_inn_room(campaign_id, db)

    inn_data = build_inn_data(campaign, db)
    # Cache the generated hero pool
    _INN_HERO_CACHE[campaign_id] = inn_data.available_heroes
    return inn_data


@router.post("/{campaign_id}/inn/purchase", response_model=PurchaseResponse)
def buy_item(
    campaign_id: int,
    body: PurchaseRequest,
    db: Session = Depends(get_db),
):
    """Purchase one or more items from the inn shop."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    _get_active_inn_room(campaign_id, db)

    return purchase_item(campaign, body.item_name, body.quantity, db)


@router.post("/{campaign_id}/inn/recruit", response_model=RecruitResponse)
def recruit(
    campaign_id: int,
    body: RecruitRequest,
    db: Session = Depends(get_db),
):
    """Recruit a hero from the inn's available pool."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    _get_active_inn_room(campaign_id, db)

    pool = _INN_HERO_CACHE.get(campaign_id, [])
    return recruit_hero(campaign, body.hero_pool_id, body.hero_name, db, pool)


@router.post("/{campaign_id}/inn/leave")
def leave_inn(campaign_id: int, db: Session = Depends(get_db)):
    """Mark the inn room as completed and prepare to advance."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    event = _get_active_inn_room(campaign_id, db)
    event.completed = True
    db.commit()

    # Clear hero pool cache
    _INN_HERO_CACHE.pop(campaign_id, None)
    return {"message": "Left the inn. Call /next-room to continue.", "room_number": event.room_number}
