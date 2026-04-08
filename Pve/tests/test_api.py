"""Integration tests hitting the FastAPI endpoints end-to-end."""
import pytest
from unittest.mock import patch
from app.models.db_models import RoomEvent, RoomType as DBRoomType, CampaignStatus
from tests.conftest import make_campaign, make_hero


class TestCampaignEndpoints:
    def test_start_campaign(self, client):
        resp = client.post("/campaign/start", json={
            "user_id": 1,
            "username": "tester",
            "hero_name": "Aldric",
            "hero_class": "warrior",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["current_room"] == 0
        assert len(data["heroes"]) == 1
        assert data["heroes"][0]["name"] == "Aldric"
        assert data["heroes"][0]["hero_class"] == "warrior"

    def test_get_campaign(self, client, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.commit()

        resp = client.get(f"/campaign/{campaign.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == campaign.id

    def test_get_nonexistent_campaign(self, client):
        resp = client.get("/campaign/999999")
        assert resp.status_code == 404

    def test_save_campaign(self, client, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.commit()

        resp = client.post(f"/campaign/{campaign.id}/save")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestMapEndpoints:
    def test_next_room_advances_room(self, client, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.commit()

        resp = client.post(f"/campaign/{campaign.id}/next-room")
        assert resp.status_code == 200
        data = resp.json()
        assert data["room_number"] == 1
        assert data["room_type"] in ("battle", "inn")

    def test_battle_room_has_enemies(self, client, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.commit()

        with patch("app.services.map_service.random.random", return_value=0.0):
            resp = client.post(f"/campaign/{campaign.id}/next-room")

        assert resp.status_code == 200
        data = resp.json()
        assert data["room_type"] == "battle"
        assert data["enemy_party"] is not None
        assert len(data["enemy_party"]) >= 1

    def test_inn_room_has_inn_data(self, client, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.commit()

        with patch("app.services.map_service.random.random", return_value=1.0):
            resp = client.post(f"/campaign/{campaign.id}/next-room")

        assert resp.status_code == 200
        data = resp.json()
        assert data["room_type"] == "inn"
        assert data["inn_data"] is not None

    def test_cannot_advance_with_pending_room(self, client, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        # Add an incomplete room event
        db.add(RoomEvent(
            campaign_id=campaign.id, room_number=1,
            room_type=DBRoomType.BATTLE, completed=False,
        ))
        campaign.current_room = 1
        db.commit()

        resp = client.post(f"/campaign/{campaign.id}/next-room")
        assert resp.status_code == 409

    def test_cannot_advance_past_30_rooms(self, client, db):
        campaign = make_campaign(db, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id)
        db.commit()

        resp = client.post(f"/campaign/{campaign.id}/next-room")
        assert resp.status_code == 400

    def test_get_current_room_no_pending(self, client, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.commit()

        resp = client.get(f"/campaign/{campaign.id}/current-room")
        assert resp.status_code == 200
        assert "No pending room" in resp.json()["message"]


class TestBattleEndpoints:
    def _setup_battle(self, db):
        campaign = make_campaign(db, room=1)
        hero = make_hero(db, campaign.id)
        db.add(RoomEvent(
            campaign_id=campaign.id, room_number=1,
            room_type=DBRoomType.BATTLE, completed=False,
        ))
        db.commit()
        db.refresh(campaign)
        return campaign, hero

    def test_submit_win_result(self, client, db):
        campaign, hero = self._setup_battle(db)

        resp = client.post(f"/campaign/{campaign.id}/battle-result", json={
            "campaign_id": campaign.id,
            "result": "win",
            "surviving_hero_ids": [hero.id],
            "enemy_party": [{"id": 1, "level": 2, "attack": 8, "defense": 7, "hp": 160, "max_hp": 160}],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "win"
        assert data["gold_change"] > 0

    def test_submit_loss_result(self, client, db):
        campaign, hero = self._setup_battle(db)

        resp = client.post(f"/campaign/{campaign.id}/battle-result", json={
            "campaign_id": campaign.id,
            "result": "loss",
            "surviving_hero_ids": [],
            "enemy_party": [{"id": 1, "level": 3, "attack": 11, "defense": 9, "hp": 190, "max_hp": 190}],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "loss"
        assert data["gold_change"] <= 0

    def test_invalid_result_rejected(self, client, db):
        campaign, hero = self._setup_battle(db)

        resp = client.post(f"/campaign/{campaign.id}/battle-result", json={
            "campaign_id": campaign.id,
            "result": "draw",
            "surviving_hero_ids": [],
            "enemy_party": [],
        })
        assert resp.status_code == 422

    def test_level_up_hero(self, client, db):
        from app.services.constants import exp_needed_for_level
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, experience=exp_needed_for_level(2))
        db.commit()

        resp = client.post(
            f"/campaign/{campaign.id}/hero/{hero.id}/level-up",
            json={"hero_id": hero.id, "class_to_level": "warrior"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["levelled_up"] is True
        assert data["hero"]["level"] == 2


class TestInnEndpoints:
    def _setup_inn(self, db):
        campaign = make_campaign(db, gold=1000, room=1)
        campaign.last_inn_room = 1
        hero = make_hero(db, campaign.id, hp=50)
        db.add(RoomEvent(
            campaign_id=campaign.id, room_number=1,
            room_type=DBRoomType.INN, completed=False,
        ))
        db.commit()
        db.refresh(campaign)
        return campaign, hero

    def test_get_inn(self, client, db):
        campaign, hero = self._setup_inn(db)

        resp = client.get(f"/campaign/{campaign.id}/inn")
        assert resp.status_code == 200
        data = resp.json()
        assert "available_items" in data
        assert len(data["available_items"]) == 7

    def test_purchase_item(self, client, db):
        campaign, hero = self._setup_inn(db)

        resp = client.post(f"/campaign/{campaign.id}/inn/purchase", json={
            "item_name": "bread", "quantity": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["gold_remaining"] == 800

    def test_purchase_with_insufficient_gold(self, client, db):
        campaign = make_campaign(db, gold=0, room=1)
        campaign.last_inn_room = 1
        make_hero(db, campaign.id)
        db.add(RoomEvent(
            campaign_id=campaign.id, room_number=1,
            room_type=DBRoomType.INN, completed=False,
        ))
        db.commit()

        resp = client.post(f"/campaign/{campaign.id}/inn/purchase", json={
            "item_name": "elixir", "quantity": 1,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_leave_inn(self, client, db):
        campaign, hero = self._setup_inn(db)

        resp = client.post(f"/campaign/{campaign.id}/inn/leave")
        assert resp.status_code == 200
        assert "Left the inn" in resp.json()["message"]


class TestScoreEndpoints:
    def test_finalize_score(self, client, db):
        campaign = make_campaign(db, gold=100, room=30)
        campaign.status = CampaignStatus.COMPLETED
        make_hero(db, campaign.id, level=5)
        db.commit()

        resp = client.post(f"/campaign/{campaign.id}/score", json={"username": "tester"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_score"] > 0
        assert data["rank"] >= 1

    def test_cannot_score_incomplete_campaign(self, client, db):
        campaign = make_campaign(db, gold=0, room=10)
        make_hero(db, campaign.id)
        db.commit()

        resp = client.post(f"/campaign/{campaign.id}/score", json={"username": "tester"})
        assert resp.status_code == 400

    def test_hall_of_fame(self, client):
        resp = client.get("/hall-of-fame")
        assert resp.status_code == 200
        assert "entries" in resp.json()

    def test_hall_of_fame_custom_limit(self, client):
        resp = client.get("/hall-of-fame?limit=5")
        assert resp.status_code == 200

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
