"""Map / room navigation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.db_models import Campaign, CampaignStatus, RoomEvent
from app.models.schemas import RoomResult
from app.services.map_service import advance_room, get_current_room_event, generate_enemy_party
from app.services.score_service import calculate_score
from app.config import settings

router = APIRouter(prefix="/campaign", tags=["map"])


@router.post("/{campaign_id}/next-room", response_model=RoomResult)
def next_room(campaign_id: int, db: Session = Depends(get_db)):
    """
    Advance the campaign to the next room.
    Returns whether the room is a battle or inn, along with relevant data.
    If this is room 30, triggers score calculation instead.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    if campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Campaign is not active.")
    if campaign.current_room >= settings.TOTAL_ROOMS:
        raise HTTPException(status_code=400, detail="Campaign already completed 30 rooms.")

    # Ensure no incomplete room is pending
    pending = get_current_room_event(campaign_id, db)
    if pending:
        raise HTTPException(
            status_code=409,
            detail=f"Room {pending.room_number} ({pending.room_type}) is not completed yet.",
        )

    result = advance_room(campaign, db)

    # If we just completed room 30, mark campaign done (score endpoint handles scoring)
    if campaign.current_room >= settings.TOTAL_ROOMS:
        campaign.status = CampaignStatus.COMPLETED
        db.commit()

    return result


@router.get("/{campaign_id}/current-room")
def current_room(campaign_id: int, db: Session = Depends(get_db)):
    """Get the details of the current (incomplete) room, if any."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    event = get_current_room_event(campaign_id, db)
    if not event:
        return {
            "campaign_id": campaign_id,
            "current_room": campaign.current_room,
            "message": "No pending room. Call /next-room to advance.",
        }
    return {
        "campaign_id": campaign_id,
        "room_number": event.room_number,
        "room_type": event.room_type,
        "completed": event.completed,
        "enemy_party": event.enemy_party_snapshot,
    }
