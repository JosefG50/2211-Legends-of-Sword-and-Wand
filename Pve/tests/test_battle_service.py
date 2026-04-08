"""Tests for battle result processing: XP/gold on win, penalties on loss."""
import pytest
from app.services.battle_service import process_battle_result
from app.models.schemas import EnemyUnit
from app.models.db_models import RoomEvent, RoomType as DBRoomType
from tests.conftest import make_campaign, make_hero


def _enemy(level: int, idx: int = 1) -> EnemyUnit:
    from app.services.constants import enemy_attack, enemy_defense, enemy_hp
    hp = enemy_hp(level)
    return EnemyUnit(id=idx, level=level, attack=enemy_attack(level),
                     defense=enemy_defense(level), hp=hp, max_hp=hp)


def _add_battle_room(db, campaign_id: int, room_number: int):
    event = RoomEvent(
        campaign_id=campaign_id,
        room_number=room_number,
        room_type=DBRoomType.BATTLE,
        completed=False,
    )
    db.add(event)
    db.flush()
    return event


class TestWinOutcome:
    def test_gold_awarded_on_win(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        hero = make_hero(db, campaign.id)
        _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        enemies = [_enemy(2, 1), _enemy(3, 2)]  # 150 + 225 = 375 gold
        result = process_battle_result(campaign, "win", [hero.id], enemies, db)

        assert result.result == "win"
        assert result.gold_change == 375
        assert campaign.gold == 375

    def test_exp_awarded_on_win(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        hero = make_hero(db, campaign.id)
        _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        enemies = [_enemy(2, 1)]  # 50 * 2 = 100 exp
        result = process_battle_result(campaign, "win", [hero.id], enemies, db)

        assert result.exp_change == 100
        db.refresh(hero)
        assert hero.experience == 100

    def test_exp_split_among_survivors(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        h1 = make_hero(db, campaign.id, name="A")
        h2 = make_hero(db, campaign.id, name="B")
        _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        enemies = [_enemy(2, 1)]  # 100 exp / 2 = 50 each
        process_battle_result(campaign, "win", [h1.id, h2.id], enemies, db)

        db.refresh(h1)
        db.refresh(h2)
        assert h1.experience == 50
        assert h2.experience == 50

    def test_dead_heroes_not_in_survivors_are_marked(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        h1 = make_hero(db, campaign.id, name="A")
        h2 = make_hero(db, campaign.id, name="B")
        _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        # Only h1 survived
        process_battle_result(campaign, "win", [h1.id], [_enemy(1, 1)], db)

        db.refresh(h2)
        assert h2.is_alive is False
        assert h2.hp == 0

    def test_room_event_marked_completed_on_win(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        hero = make_hero(db, campaign.id)
        event = _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        process_battle_result(campaign, "win", [hero.id], [_enemy(1, 1)], db)
        db.refresh(event)
        assert event.completed is True
        assert event.result == "win"


class TestLossOutcome:
    def test_gold_penalty_on_loss(self, db):
        campaign = make_campaign(db, gold=1000, room=1)
        hero = make_hero(db, campaign.id)
        _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        result = process_battle_result(campaign, "loss", [], [_enemy(1, 1)], db)

        assert result.result == "loss"
        assert result.gold_change == -100  # 10% of 1000
        assert campaign.gold == 900

    def test_exp_penalty_on_loss(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        hero = make_hero(db, campaign.id, experience=100)
        _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        process_battle_result(campaign, "loss", [], [_enemy(1, 1)], db)

        db.refresh(hero)
        assert hero.experience == 70  # 100 - 30% = 70

    def test_return_to_last_inn_on_loss(self, db):
        campaign = make_campaign(db, gold=0, room=5)
        campaign.last_inn_room = 3
        db.flush()
        hero = make_hero(db, campaign.id)
        _add_battle_room(db, campaign.id, 5)
        db.refresh(campaign)

        process_battle_result(campaign, "loss", [], [_enemy(1, 1)], db)

        assert campaign.current_room == 3

    def test_gold_cannot_go_below_zero_on_loss(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        hero = make_hero(db, campaign.id)
        _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        process_battle_result(campaign, "loss", [], [_enemy(1, 1)], db)
        assert campaign.gold == 0

    def test_room_marked_completed_on_loss(self, db):
        campaign = make_campaign(db, gold=0, room=1)
        hero = make_hero(db, campaign.id)
        event = _add_battle_room(db, campaign.id, 1)
        db.refresh(campaign)

        process_battle_result(campaign, "loss", [], [_enemy(1, 1)], db)
        db.refresh(event)
        assert event.completed is True
        assert event.result == "loss"
