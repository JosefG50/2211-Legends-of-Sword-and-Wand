"""Score calculation and hall of fame logic."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.db_models import Campaign, Score, CampaignStatus, InventoryItem
from app.models.schemas import ScoreResponse, HallOfFame, HallOfFameEntry
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def calculate_score(campaign: Campaign, username: str, db: Session) -> ScoreResponse:
    """
    Calculate and persist the final score for a completed campaign.
    Score = hero levels * 100 + gold * 10 + sum(item_price/2 * 10)
    """
    # Hero level score
    hero_level_score = sum(h.level for h in campaign.heroes) * settings.SCORE_PER_HERO_LEVEL

    # Gold score
    gold_score = campaign.gold * settings.SCORE_PER_GOLD

    # Item score: for each item bought, (purchase_price / 2) * 10 * quantity
    inventory: list[InventoryItem] = (
        db.query(InventoryItem)
        .filter(InventoryItem.campaign_id == campaign.id)
        .all()
    )
    item_score = sum(
        int(item.purchase_price / 2) * settings.SCORE_ITEM_MULTIPLIER * item.quantity
        for item in inventory
    )

    total = hero_level_score + gold_score + item_score

    # Persist (upsert)
    existing = db.query(Score).filter(Score.campaign_id == campaign.id).first()
    if existing:
        existing.total_score = total
        existing.hero_level_score = hero_level_score
        existing.gold_score = gold_score
        existing.item_score = item_score
        score_record = existing
    else:
        score_record = Score(
            campaign_id=campaign.id,
            user_id=campaign.user_id,
            username=username,
            total_score=total,
            hero_level_score=hero_level_score,
            gold_score=gold_score,
            item_score=item_score,
        )
        db.add(score_record)

    campaign.status = CampaignStatus.COMPLETED
    db.commit()
    db.refresh(score_record)

    rank = _get_rank(score_record.id, total, db)
    logger.info(f"Campaign {campaign.id} scored {total} (rank #{rank})")

    return ScoreResponse(
        campaign_id=campaign.id,
        user_id=campaign.user_id,
        username=username,
        total_score=total,
        hero_level_score=hero_level_score,
        gold_score=gold_score,
        item_score=item_score,
        rank=rank,
    )


def _get_rank(score_id: int, total_score: int, db: Session) -> int:
    """Return 1-based rank of this score among all scores."""
    count = db.query(Score).filter(Score.total_score > total_score).count()
    return count + 1


def get_hall_of_fame(db: Session, limit: int = 10) -> HallOfFame:
    scores = (
        db.query(Score)
        .order_by(desc(Score.total_score))
        .limit(limit)
        .all()
    )
    entries = [
        HallOfFameEntry(
            rank=i + 1,
            username=s.username,
            total_score=s.total_score,
            campaign_id=s.campaign_id,
        )
        for i, s in enumerate(scores)
    ]
    return HallOfFame(entries=entries)
