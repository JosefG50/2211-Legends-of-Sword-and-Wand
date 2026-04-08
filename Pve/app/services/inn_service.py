"""Inn logic: heal party, item shop, hero recruitment."""
import random
from sqlalchemy.orm import Session
from app.models.db_models import Campaign, CampaignHero, InventoryItem, HeroClass
from app.models.schemas import (
    InnData, InnItem, InnHero, PurchaseResponse, RecruitResponse,
)
from app.services.constants import INN_ITEMS, RANDOM_HERO_NAMES
from app.services.hero_service import create_hero_for_campaign, hero_to_schema
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_INN_HERO_POOL_KEY = "_inn_hero_pool"  # stored transiently per campaign room visit


def heal_party(campaign: Campaign, db: Session) -> tuple[list[str], dict, dict]:
    """
    Revive all dead heroes, restore full HP and mana.
    Returns (revived_names, healed_amounts, mana_amounts).
    """
    revived: list[str] = []
    healed: dict[str, int] = {}
    mana_restored: dict[str, int] = {}

    for hero in campaign.heroes:
        if not hero.is_alive:
            hero.is_alive = True
            hero.hp = hero.max_hp
            hero.mana = hero.max_mana
            revived.append(hero.name)
            healed[hero.name] = hero.max_hp
            mana_restored[hero.name] = hero.max_mana
        else:
            hp_gain = hero.max_hp - hero.hp
            mana_gain = hero.max_mana - hero.mana
            hero.hp = hero.max_hp
            hero.mana = hero.max_mana
            healed[hero.name] = hp_gain
            mana_restored[hero.name] = mana_gain

    db.flush()
    return revived, healed, mana_restored


def _generate_inn_heroes(campaign: Campaign) -> list[InnHero]:
    """Generate a random pool of recruitable heroes (rooms 1-10 only)."""
    if campaign.current_room > settings.INN_HERO_RECRUITMENT_ROOMS:
        return []
    if len(campaign.heroes) >= settings.MAX_PARTY_SIZE:
        return []

    base_classes = ["order", "chaos", "warrior", "mage"]
    pool_size = random.randint(1, 3)
    used_names = {h.name for h in campaign.heroes}
    pool: list[InnHero] = []

    for i in range(pool_size):
        level = random.randint(1, 4)
        cost = 0 if level == 1 else 200 * level
        name = random.choice([n for n in RANDOM_HERO_NAMES if n not in used_names])
        used_names.add(name)
        pool.append(InnHero(
            id=f"pool_{i}_{name}",
            name=name,
            hero_class=random.choice(base_classes),
            level=level,
            recruit_cost=cost,
        ))
    return pool


def build_inn_data(campaign: Campaign, db: Session) -> InnData:
    """Heal party and build the full InnData payload."""
    revived, healed, mana_restored = heal_party(campaign, db)
    heroes_pool = _generate_inn_heroes(campaign)

    # Cache pool on campaign object for later recruitment calls
    campaign.__dict__[_INN_HERO_POOL_KEY] = heroes_pool

    return InnData(
        revived_heroes=revived,
        healed_heroes=healed,
        mana_restored=mana_restored,
        available_items=list(INN_ITEMS.values()),
        available_heroes=heroes_pool,
        party_full=(len(campaign.heroes) >= settings.MAX_PARTY_SIZE),
    )


def purchase_item(
    campaign: Campaign,
    item_name: str,
    quantity: int,
    db: Session,
) -> PurchaseResponse:
    """Buy an item from the inn shop."""
    item_name = item_name.lower()
    item = INN_ITEMS.get(item_name)
    if not item:
        return PurchaseResponse(
            success=False,
            message=f"Unknown item: {item_name}",
            gold_remaining=campaign.gold,
            item_name=item_name,
            quantity=0,
        )

    total_cost = item.cost * quantity
    if campaign.gold < total_cost:
        return PurchaseResponse(
            success=False,
            message=f"Not enough gold. Need {total_cost}g, have {campaign.gold}g.",
            gold_remaining=campaign.gold,
            item_name=item_name,
            quantity=0,
        )

    campaign.gold -= total_cost

    # Record in inventory
    existing = (
        db.query(InventoryItem)
        .filter(InventoryItem.campaign_id == campaign.id, InventoryItem.item_name == item_name)
        .first()
    )
    if existing:
        existing.quantity += quantity
    else:
        db.add(InventoryItem(
            campaign_id=campaign.id,
            item_name=item_name,
            quantity=quantity,
            purchase_price=item.cost,
        ))

    db.commit()
    logger.info(f"Campaign {campaign.id} purchased {quantity}x {item_name} for {total_cost}g")
    return PurchaseResponse(
        success=True,
        message=f"Purchased {quantity}x {item_name} for {total_cost}g.",
        gold_remaining=campaign.gold,
        item_name=item_name,
        quantity=quantity,
    )


def recruit_hero(
    campaign: Campaign,
    hero_pool_id: str,
    hero_name: str,
    db: Session,
    inn_hero_pool: list[InnHero],
) -> RecruitResponse:
    """Recruit a hero from the inn pool."""
    if len(campaign.heroes) >= settings.MAX_PARTY_SIZE:
        return RecruitResponse(
            success=False,
            message="Party is full (max 5 heroes).",
            gold_remaining=campaign.gold,
        )

    # Find the hero in the pool by id
    pool_hero = next((h for h in inn_hero_pool if h.id == hero_pool_id), None)
    if not pool_hero:
        return RecruitResponse(
            success=False,
            message="Hero not found in recruitment pool.",
            gold_remaining=campaign.gold,
        )

    if campaign.gold < pool_hero.recruit_cost:
        return RecruitResponse(
            success=False,
            message=f"Not enough gold. Need {pool_hero.recruit_cost}g, have {campaign.gold}g.",
            gold_remaining=campaign.gold,
        )

    campaign.gold -= pool_hero.recruit_cost

    # Create and persist the hero
    new_hero = create_hero_for_campaign(
        campaign_id=campaign.id,
        name=hero_name or pool_hero.name,
        hero_class=pool_hero.hero_class,
        level=pool_hero.level,
        db=db,
    )
    db.commit()
    db.refresh(new_hero)

    logger.info(f"Campaign {campaign.id} recruited {new_hero.name} (level {new_hero.level})")
    return RecruitResponse(
        success=True,
        message=f"Recruited {new_hero.name} for {pool_hero.recruit_cost}g.",
        gold_remaining=campaign.gold,
        hero=hero_to_schema(new_hero),
    )
