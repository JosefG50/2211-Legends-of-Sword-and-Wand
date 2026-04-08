"""Tests for map service: battle chance, enemy generation, room advancement."""
import pytest
from unittest.mock import patch
from app.services.map_service import compute_battle_chance, generate_enemy_party
from app.services.constants import enemy_attack, enemy_defense, enemy_hp
from tests.conftest import make_campaign, make_hero


class TestBattleChance:
    def test_base_chance_zero_levels(self):
        assert compute_battle_chance(0) == pytest.approx(0.60)

    def test_no_shift_below_10_levels(self):
        assert compute_battle_chance(9) == pytest.approx(0.60)

    def test_shift_at_10_levels(self):
        assert compute_battle_chance(10) == pytest.approx(0.63)

    def test_shift_at_20_levels(self):
        assert compute_battle_chance(20) == pytest.approx(0.66)

    def test_shift_at_100_levels(self):
        # 100 levels → 10 shifts of 3% = +30% → 90%
        assert compute_battle_chance(100) == pytest.approx(0.90)

    def test_capped_at_90_percent(self):
        # Even at 200 cumulative levels, chance should not exceed 90%
        assert compute_battle_chance(200) == pytest.approx(0.90)

    def test_monotonic_increase(self):
        chances = [compute_battle_chance(lvl) for lvl in range(0, 110, 10)]
        for i in range(1, len(chances)):
            assert chances[i] >= chances[i - 1]


class TestEnemyGeneration:
    def test_generates_1_to_5_units(self):
        for _ in range(50):
            party = generate_enemy_party(10)
            assert 1 <= len(party) <= 5

    def test_unit_levels_between_1_and_10(self):
        for _ in range(30):
            party = generate_enemy_party(15)
            for unit in party:
                assert 1 <= unit.level <= 10

    def test_stats_scale_with_level(self):
        low_party = generate_enemy_party(1)
        high_party = generate_enemy_party(50)
        avg_low_hp = sum(u.hp for u in low_party) / len(low_party)
        avg_high_hp = sum(u.hp for u in high_party) / len(high_party)
        # Higher level enemies should generally have more HP on average
        # (probabilistic, so we test the formulas directly)
        assert enemy_hp(1) < enemy_hp(10)
        assert enemy_attack(1) < enemy_attack(10)
        assert enemy_defense(1) < enemy_defense(10)

    def test_unit_has_required_fields(self):
        party = generate_enemy_party(5)
        for unit in party:
            assert unit.id > 0
            assert unit.hp > 0
            assert unit.max_hp == unit.hp
            assert unit.attack >= 0
            assert unit.defense >= 0
            assert unit.is_alive is True
            assert unit.is_stunned is False

    def test_all_units_alive_on_creation(self):
        party = generate_enemy_party(10)
        assert all(u.is_alive for u in party)

    def test_ids_are_unique(self):
        party = generate_enemy_party(20)
        ids = [u.id for u in party]
        assert len(ids) == len(set(ids))

    def test_low_player_level_yields_lower_enemies(self):
        """With player cumulative level 1, enemy levels should all be 1."""
        # Run many times; every run should produce level 1 enemies for pcl=1
        for _ in range(20):
            party = generate_enemy_party(1)
            for unit in party:
                assert unit.level == 1


class TestAdvanceRoom:
    def test_advance_room_increments_room_number(self, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.refresh(campaign)

        from app.services.map_service import advance_room
        result = advance_room(campaign, db)
        assert result.room_number == 1
        assert campaign.current_room == 1

    def test_advance_room_returns_valid_type(self, db):
        from app.services.map_service import advance_room
        from app.models.schemas import RoomType
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.refresh(campaign)

        result = advance_room(campaign, db)
        assert result.room_type in (RoomType.BATTLE, RoomType.INN)

    def test_battle_room_has_enemy_party(self, db):
        from app.services.map_service import advance_room
        from app.models.schemas import RoomType
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.refresh(campaign)

        # Force a battle room
        with patch("app.services.map_service.random.random", return_value=0.0):
            result = advance_room(campaign, db)

        assert result.room_type == RoomType.BATTLE
        assert result.enemy_party is not None
        assert len(result.enemy_party) >= 1

    def test_inn_room_has_inn_data(self, db):
        from app.services.map_service import advance_room
        from app.models.schemas import RoomType
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.refresh(campaign)

        # Force an inn room
        with patch("app.services.map_service.random.random", return_value=1.0):
            result = advance_room(campaign, db)

        assert result.room_type == RoomType.INN
        assert result.inn_data is not None

    def test_inn_sets_last_inn_room(self, db):
        from app.services.map_service import advance_room
        campaign = make_campaign(db)
        make_hero(db, campaign.id)
        db.refresh(campaign)

        with patch("app.services.map_service.random.random", return_value=1.0):
            advance_room(campaign, db)

        assert campaign.last_inn_room == 1
