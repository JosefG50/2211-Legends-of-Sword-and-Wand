"""Tests for hero levelling, class gains, specialisation and hybrid classes."""
import pytest
from app.services.hero_service import try_level_up, create_hero_for_campaign, hero_to_schema
from app.services.constants import exp_needed_for_level, CLASS_GAINS, LEVEL_BASE_GAINS
from app.models.db_models import HeroClass
from tests.conftest import make_campaign, make_hero


class TestExpFormula:
    def test_level_2_exp(self):
        # Exp(2) = 500 + 75*2 + 20*4 = 500 + 150 + 80 = 730
        assert exp_needed_for_level(2) == 730

    def test_level_3_exp_cumulative(self):
        # Exp(3) = Exp(2) + 500 + 75*3 + 20*9 = 730 + 500 + 225 + 180 = 1635
        assert exp_needed_for_level(3) == 1635

    def test_exp_increases_with_level(self):
        for l in range(2, 20):
            assert exp_needed_for_level(l) < exp_needed_for_level(l + 1)


class TestLevelUp:
    def test_level_up_succeeds_with_enough_exp(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, experience=exp_needed_for_level(2))

        did_up, msg = try_level_up(hero, "warrior", db)
        assert did_up is True
        assert hero.level == 2

    def test_level_up_fails_without_exp(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, experience=0)

        did_up, msg = try_level_up(hero, "warrior", db)
        assert did_up is False
        assert hero.level == 1

    def test_level_up_consumes_experience(self, db):
        campaign = make_campaign(db)
        needed = exp_needed_for_level(2)
        hero = make_hero(db, campaign.id, experience=needed + 200)

        try_level_up(hero, "warrior", db)
        assert hero.experience == 200

    def test_warrior_gains_attack_and_defense(self, db):
        campaign = make_campaign(db)
        needed = exp_needed_for_level(2)
        hero = make_hero(db, campaign.id, experience=needed)
        atk_before, def_before = hero.attack, hero.defense

        try_level_up(hero, "warrior", db)

        expected_atk = atk_before + LEVEL_BASE_GAINS["attack"] + CLASS_GAINS["warrior"].get("attack", 0)
        expected_def = def_before + LEVEL_BASE_GAINS["defense"] + CLASS_GAINS["warrior"].get("defense", 0)
        assert hero.attack == expected_atk
        assert hero.defense == expected_def

    def test_order_gains_mana_and_defense(self, db):
        campaign = make_campaign(db)
        needed = exp_needed_for_level(2)
        hero = make_hero(db, campaign.id, hero_class="order", experience=needed)
        mana_before, def_before = hero.mana, hero.defense

        try_level_up(hero, "order", db)

        assert hero.mana == mana_before + LEVEL_BASE_GAINS["mana"] + CLASS_GAINS["order"].get("mana", 0)
        assert hero.defense == def_before + LEVEL_BASE_GAINS["defense"] + CLASS_GAINS["order"].get("defense", 0)

    def test_max_level_20_blocks_level_up(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, level=20, experience=999999)
        hero.level = 20
        db.flush()

        did_up, msg = try_level_up(hero, "warrior", db)
        assert did_up is False
        assert "max level" in msg.lower()

    def test_class_levels_tracked(self, db):
        campaign = make_campaign(db)
        needed = exp_needed_for_level(2)
        hero = make_hero(db, campaign.id, hero_class="warrior", experience=needed)
        hero.class_levels = {"warrior": 1}
        db.flush()

        try_level_up(hero, "chaos", db)
        assert hero.class_levels.get("chaos", 0) == 1


class TestSpecialization:
    def _level_hero_to_5_in_class(self, hero, hero_class: str, db):
        """Helper: give hero enough exp to level up 4 more times in a class."""
        hero.class_levels = {hero_class: 1}
        db.flush()
        for target_level in range(2, 6):
            hero.experience += exp_needed_for_level(target_level)
            try_level_up(hero, hero_class, db)

    def test_specialization_granted_at_level_5(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, hero_class="warrior")
        self._level_hero_to_5_in_class(hero, "warrior", db)

        assert hero.class_levels.get("warrior", 0) >= 5
        assert hero.specialization is not None

    def test_no_specialization_before_level_5(self, db):
        campaign = make_campaign(db)
        needed = exp_needed_for_level(2)
        hero = make_hero(db, campaign.id, hero_class="warrior", experience=needed)
        try_level_up(hero, "warrior", db)  # level 2 only
        assert hero.specialization is None


class TestHybridClass:
    def _max_class(self, hero, hero_class: str, db):
        hero.class_levels = dict(hero.class_levels or {})
        hero.class_levels[hero_class] = 5
        db.flush()

    def test_hybrid_formed_when_two_classes_at_5(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, hero_class="warrior")
        # Manually set two classes to level 5
        hero.class_levels = {"warrior": 5, "mage": 5}
        hero.level = 10
        db.flush()

        # Trigger hybrid check
        from app.services.hero_service import _check_hybrid
        _check_hybrid(hero)

        assert hero.is_hybrid is True
        assert hero.hero_class.value == "warlock"

    def test_specialization_lost_on_hybrid(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, hero_class="warrior")
        hero.class_levels = {"warrior": 5, "mage": 5}
        hero.specialization = HeroClass.WARRIOR
        hero.level = 10
        db.flush()

        from app.services.hero_service import _check_hybrid
        _check_hybrid(hero)

        assert hero.specialization is None

    def test_order_chaos_becomes_heretic(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, hero_class="order")
        hero.class_levels = {"order": 5, "chaos": 5}
        hero.level = 10
        db.flush()

        from app.services.hero_service import _check_hybrid
        _check_hybrid(hero)

        assert hero.hero_class.value == "heretic"


class TestCreateHero:
    def test_base_stats_at_level_1(self, db):
        campaign = make_campaign(db)
        hero = create_hero_for_campaign(campaign.id, "Test", "warrior", level=1, db=db)

        assert hero.attack == 5
        assert hero.defense == 5
        assert hero.hp == 100
        assert hero.mana == 50

    def test_hero_schema_conversion(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id)
        schema = hero_to_schema(hero)

        assert schema.id == hero.id
        assert schema.name == hero.name
        assert schema.level == hero.level
