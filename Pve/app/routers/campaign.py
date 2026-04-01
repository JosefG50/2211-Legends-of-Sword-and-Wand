"""Campaign CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.db_models import Campaign, CampaignStatus
from app.models.schemas import (
    CampaignCreate, CampaignState, SaveResponse, SavePartyRequest, SavePartyResponse,
)
from app.services.hero_service import create_hero_for_campaign, hero_to_schema
from app.config import settings

router = APIRouter(prefix="/campaign", tags=["campaign"])


def _campaign_or_404(campaign_id: int, db: Session) -> Campaign:
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found.")
    return c


@router.post("/start", response_model=CampaignState, status_code=201)
def start_campaign(body: CampaignCreate, db: Session = Depends(get_db)):
    """Start a new PvE campaign with a single starting hero."""
    campaign = Campaign(
        user_id=body.user_id,
        status=CampaignStatus.ACTIVE,
        current_room=0,
        gold=0,
        last_inn_room=0,
    )
    db.add(campaign)
    db.flush()

    create_hero_for_campaign(
        campaign_id=campaign.id,
        name=body.hero_name,
        hero_class=body.hero_class.value,
        level=1,
        db=db,
    )
    db.commit()
    db.refresh(campaign)

    return CampaignState(
        id=campaign.id,
        user_id=campaign.user_id,
        status=campaign.status,
        current_room=campaign.current_room,
        gold=campaign.gold,
        last_inn_room=campaign.last_inn_room,
        heroes=[hero_to_schema(h) for h in campaign.heroes],
    )


@router.get("/{campaign_id}", response_model=CampaignState)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get current state of a campaign (resume support)."""
    campaign = _campaign_or_404(campaign_id, db)
    return CampaignState(
        id=campaign.id,
        user_id=campaign.user_id,
        status=campaign.status,
        current_room=campaign.current_room,
        gold=campaign.gold,
        last_inn_room=campaign.last_inn_room,
        heroes=[hero_to_schema(h) for h in campaign.heroes],
    )


@router.post("/{campaign_id}/save", response_model=SaveResponse)
def save_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Save & exit the campaign. Can only be done outside of battle
    (at inn or between rooms).
    """
    campaign = _campaign_or_404(campaign_id, db)
    if campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Campaign is not active.")

    # State is already persisted continuously; just acknowledge save
    db.commit()
    return SaveResponse(
        success=True,
        message="Campaign progress saved. You can resume at any time.",
        campaign_id=campaign_id,
    )
