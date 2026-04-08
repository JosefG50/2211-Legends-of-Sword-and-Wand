"""Hero stat and level management logic."""
from sqlalchemy.orm import Session
from app.models.db_models import CampaignHero, HeroClass
from app.models.schemas import HeroStats, LevelUpResponse
from app.services.constants import (
    HERO_BASE_STATS, LEVEL_BASE_GAINS, CLASS_GAINS,
    HYBRID_GAINS, HYBRID_CLASS_MAP, exp_needed_for_level,
)
import logging

logger = logging.getLogger(__name__)

BASE_CLASSES = {"order", "chaos", "warrior", "mage"}


def _get_class_gains(hero: CampaignHero) -> dict:
    """Return per-level stat gains for the hero's current class situation."""
    if hero.is_hybrid:
        # Find which two base classes are at level 5
        maxed = [c for c, lvl in (hero.class_levels or {}).items() if lvl >= 5 and c in BASE_CLASSES]
        if len(maxed) >= 2:
            key = (maxed[0], maxed[1])
            rev = (maxed[1], maxed[0])
            return HYBRID_GAINS.get(key) or HYBRID_GAINS.get(rev) or {}
    # Specialisation: double gains if one class is maxed
    spec_val = hero.specialization.value if hero.specialization else None
    if spec_val and spec_val in CLASS_GAINS:
        base = CLASS_GAINS[spec_val]
        return {k: v * 2 for k, v in base.items()}
    # Normal: use the hero's current class .value for lookup
    class_val = hero.hero_class.value if hasattr(hero.hero_class, "value") else str(hero.hero_class)
    return CLASS_GAINS.get(class_val, {})


def apply_level_gains(hero: CampaignHero, class_levelled: str) -> None:
    """Apply base + class stat gains for one level-up."""
    hero.attack   += LEVEL_BASE_GAINS["attack"]
    hero.defense  += LEVEL_BASE_GAINS["defense"]
    hero.max_hp   += LEVEL_BASE_GAINS["hp"]
    hero.hp       += LEVEL_BASE_GAINS["hp"]
    hero.max_mana += LEVEL_BASE_GAINS["mana"]
    hero.mana     += LEVEL_BASE_GAINS["mana"]

    gains = _get_class_gains(hero)
    hero.attack   += gains.get("attack", 0)
    hero.defense  += gains.get("defense", 0)
    hero.max_hp   += gains.get("hp", 0)
    hero.hp       += gains.get("hp", 0)
    hero.max_mana += gains.get("mana", 0)
    hero.mana     += gains.get("mana", 0)

    hero.level += 1


def _check_specialization(hero: CampaignHero, class_levelled: str) -> None:
    """Grant specialization when a base class hits level 5."""
    if hero.is_hybrid:
        return
    class_levels = hero.class_levels or {}
    if class_levels.get(class_levelled, 0) >= 5 and hero.specialization is None:
        # Map base class → its own specialization (same class name used as sentinel)
        spec_map = {
            "order": HeroClass.ORDER,
            "chaos": HeroClass.CHAOS,
            "warrior": HeroClass.WARRIOR,
            "mage": HeroClass.MAGE,
        }
        hero.specialization = spec_map.get(class_levelled)
        logger.info(f"Hero {hero.name} gained specialization: {hero.specialization}")


def _check_hybrid(hero: CampaignHero) -> None:
    """Convert hero to hybrid class when two base classes each reach level 5."""
    if hero.is_hybrid:
        return
    class_levels = hero.class_levels or {}
    maxed = [c for c, lvl in class_levels.items() if lvl >= 5 and c in BASE_CLASSES]
    if len(maxed) >= 2:
        key = frozenset(maxed[:2])
        hybrid_name = HYBRID_CLASS_MAP.get(key)
        if hybrid_name:
            hero.is_hybrid = True
            hero.specialization = None  # lose specialization bonus
            hero.hero_class = HeroClass(hybrid_name)
            logger.info(f"Hero {hero.name} became hybrid: {hybrid_name}")


def try_level_up(hero: CampaignHero, class_to_level: str, db: Session) -> tuple[bool, str]:
    """
    Attempt to level up a hero in a given class.
    Returns (did_level_up, message).
    """
    if hero.level >= 20:
        return False, "Hero is already at max level (20)."

    class_levels: dict = dict(hero.class_levels or {})
    class_levels[class_to_level] = class_levels.get(class_to_level, 0) + 1

    exp_required = exp_needed_for_level(hero.level + 1)
    if hero.experience < exp_required:
        return False, f"Not enough experience. Need {exp_required}, have {hero.experience}."

    # Consume experience
    hero.experience -= exp_required
    hero.class_levels = class_levels

    apply_level_gains(hero, class_to_level)
    _check_specialization(hero, class_to_level)
    _check_hybrid(hero)

    db.commit()
    db.refresh(hero)
    return True, f"Hero {hero.name} levelled up to {hero.level}!"


def create_hero_for_campaign(
    campaign_id: int,
    name: str,
    hero_class: str,
    level: int = 1,
    db: Session = None,
) -> CampaignHero:
    """Create a new hero with base stats and given class."""
    hero = CampaignHero(
        campaign_id=campaign_id,
        name=name,
        hero_class=HeroClass(hero_class),
        level=1,
        experience=0,
        attack=HERO_BASE_STATS["attack"],
        defense=HERO_BASE_STATS["defense"],
        hp=HERO_BASE_STATS["hp"],
        max_hp=HERO_BASE_STATS["hp"],
        mana=HERO_BASE_STATS["mana"],
        max_mana=HERO_BASE_STATS["mana"],
        is_alive=True,
        is_stunned=False,
        class_levels={hero_class: 1},
    )
    # Apply level gains for levels 2..level
    for _ in range(1, level):
        hero.level -= 1  # apply_level_gains increments
        apply_level_gains(hero, hero_class)
        _check_specialization(hero, hero_class)
        _check_hybrid(hero)

    if db:
        db.add(hero)
        db.flush()
    return hero


def hero_to_schema(hero: CampaignHero) -> HeroStats:
    return HeroStats(
        id=hero.id,
        name=hero.name,
        hero_class=hero.hero_class,
        level=hero.level,
        experience=hero.experience,
        attack=hero.attack,
        defense=hero.defense,
        hp=hero.hp,
        max_hp=hero.max_hp,
        mana=hero.mana,
        max_mana=hero.max_mana,
        is_alive=hero.is_alive,
        is_stunned=hero.is_stunned,
        class_levels=hero.class_levels or {},
        specialization=hero.specialization,
        is_hybrid=hero.is_hybrid,
    )
