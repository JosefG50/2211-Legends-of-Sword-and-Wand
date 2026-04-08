"""Tests for inn service: healing, item purchases, hero recruitment."""
import pytest
from app.services.inn_service import heal_party, purchase_item, recruit_hero, build_inn_data
from app.models.schemas import InnHero
from tests.conftest import make_campaign, make_hero


class TestHealParty:
    def test_dead_hero_is_revived(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, hp=0, is_alive=False)
        db.refresh(campaign)

        revived, healed, mana = heal_party(campaign, db)
        assert hero.name in revived
        assert hero.is_alive is True
        assert hero.hp == hero.max_hp

    def test_living_hero_is_fully_healed(self, db):
        campaign = make_campaign(db)
        hero = make_hero(db, campaign.id, hp=30, mana=10)
        db.refresh(campaign)

        _, healed, mana_restored = heal_party(campaign, db)
        assert hero.hp == hero.max_hp
        assert hero.mana == hero.max_mana
        assert healed[hero.name] == hero.max_hp - 30
        assert mana_restored[hero.name] == hero.max_mana - 10

    def test_multiple_heroes_all_healed(self, db):
        campaign = make_campaign(db)
        make_hero(db, campaign.id, name="Alpha", hp=10)
        make_hero(db, campaign.id, name="Beta", hp=50, is_alive=False)
        db.refresh(campaign)

        revived, healed, _ = heal_party(campaign, db)
        assert "Beta" in revived
        for hero in campaign.heroes:
            assert hero.hp == hero.max_hp
            assert hero.mana == hero.max_mana


class TestPurchaseItem:
    def test_successful_purchase_deducts_gold(self, db):
        campaign = make_campaign(db, gold=500)
        resp = purchase_item(campaign, "bread", 1, db)
        assert resp.success is True
        assert campaign.gold == 300  # 500 - 200

    def test_insufficient_gold_fails(self, db):
        campaign = make_campaign(db, gold=100)
        resp = purchase_item(campaign, "steak", 1, db)
        assert resp.success is False
        assert campaign.gold == 100

    def test_unknown_item_fails(self, db):
        campaign = make_campaign(db, gold=9999)
        resp = purchase_item(campaign, "dragon_scale", 1, db)
        assert resp.success is False

    def test_multiple_quantity_purchase(self, db):
        campaign = make_campaign(db, gold=1000)
        resp = purchase_item(campaign, "bread", 3, db)  # 3 × 200 = 600
        assert resp.success is True
        assert campaign.gold == 400

    def test_purchase_creates_inventory_record(self, db):
        from app.models.db_models import InventoryItem
        campaign = make_campaign(db, gold=500)
        purchase_item(campaign, "bread", 1, db)
        inv = db.query(InventoryItem).filter(InventoryItem.campaign_id == campaign.id).first()
        assert inv is not None
        assert inv.item_name == "bread"
        assert inv.quantity == 1

    def test_repeated_purchase_increments_quantity(self, db):
        from app.models.db_models import InventoryItem
        campaign = make_campaign(db, gold=9999)
        purchase_item(campaign, "water", 2, db)
        purchase_item(campaign, "water", 1, db)
        inv = db.query(InventoryItem).filter(
            InventoryItem.campaign_id == campaign.id,
            InventoryItem.item_name == "water",
        ).first()
        assert inv.quantity == 3

    def test_all_items_purchasable(self, db):
        items = ["bread", "cheese", "steak", "water", "juice", "wine", "elixir"]
        for item in items:
            campaign = make_campaign(db, gold=99999)
            resp = purchase_item(campaign, item, 1, db)
            assert resp.success is True, f"Failed to purchase {item}"


class TestRecruitHero:
    def _pool(self):
        return [
            InnHero(id="pool_0_Lyra", name="Lyra", hero_class="mage", level=1, recruit_cost=0),
            InnHero(id="pool_1_Kael", name="Kael", hero_class="warrior", level=3, recruit_cost=600),
        ]

    def test_free_level_1_hero_recruitment(self, db):
        campaign = make_campaign(db, gold=0)
        make_hero(db, campaign.id, name="Alpha")
        db.refresh(campaign)

        pool = self._pool()
        resp = recruit_hero(campaign, "pool_0_Lyra", "Lyra", db, pool)
        assert resp.success is True
        assert campaign.gold == 0
        assert resp.hero is not None

    def test_paid_hero_deducts_gold(self, db):
        campaign = make_campaign(db, gold=1000)
        make_hero(db, campaign.id, name="Alpha")
        db.refresh(campaign)

        pool = self._pool()
        resp = recruit_hero(campaign, "pool_1_Kael", "Kael", db, pool)
        assert resp.success is True
        assert campaign.gold == 400  # 1000 - 600

    def test_insufficient_gold_prevents_recruitment(self, db):
        campaign = make_campaign(db, gold=100)
        make_hero(db, campaign.id, name="Alpha")
        db.refresh(campaign)

        pool = self._pool()
        resp = recruit_hero(campaign, "pool_1_Kael", "Kael", db, pool)
        assert resp.success is False
        assert campaign.gold == 100

    def test_full_party_blocks_recruitment(self, db):
        campaign = make_campaign(db, gold=9999)
        for i in range(5):
            make_hero(db, campaign.id, name=f"Hero{i}")
        db.refresh(campaign)

        pool = self._pool()
        resp = recruit_hero(campaign, "pool_0_Lyra", "Lyra", db, pool)
        assert resp.success is False

    def test_invalid_pool_id_fails(self, db):
        campaign = make_campaign(db, gold=9999)
        make_hero(db, campaign.id, name="Alpha")
        db.refresh(campaign)

        resp = recruit_hero(campaign, "nonexistent_id", "Nobody", db, [])
        assert resp.success is False
