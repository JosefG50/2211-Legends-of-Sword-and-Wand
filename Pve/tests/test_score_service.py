"""Tests for score calculation and hall of fame."""
import pytest
from app.services.score_service import calculate_score, get_hall_of_fame
from app.models.db_models import CampaignStatus, InventoryItem
from tests.conftest import make_campaign, make_hero


class TestScoreCalculation:
    def test_hero_level_score(self, db):
        campaign = make_campaign(db, gold=0, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id, level=5)
        make_hero(db, campaign.id, name="B", level=3)
        db.refresh(campaign)

        # 8 levels × 100 = 800
        result = calculate_score(campaign, "testuser", db)
        assert result.hero_level_score == 800

    def test_gold_score(self, db):
        campaign = make_campaign(db, gold=250, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id)
        db.refresh(campaign)

        # 250 × 10 = 2500
        result = calculate_score(campaign, "testuser", db)
        assert result.gold_score == 2500

    def test_item_score(self, db):
        campaign = make_campaign(db, gold=0, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id)

        # Bread: cost=200, score = (200/2) * 10 * 2 = 2000
        db.add(InventoryItem(campaign_id=campaign.id, item_name="bread", quantity=2, purchase_price=200))
        db.flush()
        db.refresh(campaign)

        result = calculate_score(campaign, "testuser", db)
        assert result.item_score == 2000

    def test_total_is_sum_of_parts(self, db):
        campaign = make_campaign(db, gold=100, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id, level=2)
        db.add(InventoryItem(campaign_id=campaign.id, item_name="water", quantity=1, purchase_price=150))
        db.flush()
        db.refresh(campaign)

        result = calculate_score(campaign, "testuser", db)
        assert result.total_score == result.hero_level_score + result.gold_score + result.item_score

    def test_score_persisted_to_db(self, db):
        from app.models.db_models import Score
        campaign = make_campaign(db, gold=0, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id)
        db.refresh(campaign)

        calculate_score(campaign, "testuser", db)
        record = db.query(Score).filter(Score.campaign_id == campaign.id).first()
        assert record is not None
        assert record.username == "testuser"

    def test_campaign_marked_completed(self, db):
        campaign = make_campaign(db, gold=0, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id)
        db.refresh(campaign)

        calculate_score(campaign, "testuser", db)
        assert campaign.status == CampaignStatus.COMPLETED

    def test_rank_1_for_first_entry(self, db):
        campaign = make_campaign(db, gold=0, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id)
        db.refresh(campaign)

        result = calculate_score(campaign, "testuser", db)
        assert result.rank == 1


class TestHallOfFame:
    def test_hall_of_fame_returns_entries(self, db):
        from app.models.db_models import Score
        db.add(Score(campaign_id=9001, user_id=1, username="alice", total_score=5000,
                     hero_level_score=3000, gold_score=1000, item_score=1000))
        db.add(Score(campaign_id=9002, user_id=2, username="bob", total_score=3000,
                     hero_level_score=2000, gold_score=500, item_score=500))
        db.flush()

        hof = get_hall_of_fame(db, limit=10)
        usernames = [e.username for e in hof.entries]
        assert "alice" in usernames
        assert "bob" in usernames

    def test_hall_of_fame_ordered_by_score(self, db):
        from app.models.db_models import Score
        db.add(Score(campaign_id=9003, user_id=3, username="charlie", total_score=1000,
                     hero_level_score=500, gold_score=300, item_score=200))
        db.add(Score(campaign_id=9004, user_id=4, username="dave", total_score=9000,
                     hero_level_score=5000, gold_score=2000, item_score=2000))
        db.flush()

        hof = get_hall_of_fame(db, limit=10)
        scores = [e.total_score for e in hof.entries]
        assert scores == sorted(scores, reverse=True)

    def test_hall_of_fame_respects_limit(self, db):
        from app.models.db_models import Score
        for i in range(5):
            db.add(Score(campaign_id=9100 + i, user_id=10 + i, username=f"player{i}",
                         total_score=i * 100,
                         hero_level_score=i * 50, gold_score=i * 30, item_score=i * 20))
        db.flush()

        hof = get_hall_of_fame(db, limit=3)
        assert len(hof.entries) <= 3
