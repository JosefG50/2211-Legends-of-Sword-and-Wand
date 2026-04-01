"""Score and hall of fame endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.db_models import Campaign, CampaignStatus
from app.models.schemas import ScoreResponse, HallOfFame, SavePartyRequest, SavePartyResponse
from app.services.score_service import calculate_score, get_hall_of_fame
from pydantic import BaseModel

router = APIRouter(tags=["score"])


class ScoreRequest(BaseModel):
    username: str


@router.post("/campaign/{campaign_id}/score", response_model=ScoreResponse)
def finalize_score(
    campaign_id: int,
    body: ScoreRequest,
    db: Session = Depends(get_db),
):
    """
    Calculate and persist the final score for a completed campaign.
    Called after room 30 is finished.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    if campaign.current_room < 30 and campaign.status != CampaignStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign is only on room {campaign.current_room}. Must complete all 30 rooms.",
        )

    return calculate_score(campaign, body.username, db)


@router.get("/hall-of-fame", response_model=HallOfFame)
def hall_of_fame(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    """Get the top scores across all campaigns."""
    return get_hall_of_fame(db, limit=limit)
