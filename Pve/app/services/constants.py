from app.models.schemas import InnItem

INN_ITEMS: dict[str, InnItem] = {
    "bread": InnItem(
        name="bread",
        cost=200,
        effect="+20 HP",
        hp_effect=20,
    ),
    "cheese": InnItem(
        name="cheese",
        cost=500,
        effect="+50 HP",
        hp_effect=50,
    ),
    "steak": InnItem(
        name="steak",
        cost=1000,
        effect="+200 HP",
        hp_effect=200,
    ),
    "water": InnItem(
        name="water",
        cost=150,
        effect="+10 mana",
        mana_effect=10,
    ),
    "juice": InnItem(
        name="juice",
        cost=400,
        effect="+30 mana",
        mana_effect=30,
    ),
    "wine": InnItem(
        name="wine",
        cost=750,
        effect="+100 mana",
        mana_effect=100,
    ),
    "elixir": InnItem(
        name="elixir",
        cost=2000,
        effect="Revive + Full HP + Full mana",
        is_revive=True,
    ),
}

# Base stats every hero starts with at level 1
HERO_BASE_STATS = {
    "attack": 5,
    "defense": 5,
    "hp": 100,
    "mana": 50,
}

# Per-level base gains (before class bonus)
LEVEL_BASE_GAINS = {
    "attack": 1,
    "defense": 1,
    "hp": 5,
    "mana": 2,
}

# Per-level class gains
CLASS_GAINS = {
    "order":   {"mana": 5, "defense": 2},
    "chaos":   {"attack": 3, "hp": 5},
    "warrior": {"attack": 2, "defense": 3},
    "mage":    {"mana": 5, "attack": 1},
}

# Hybrid class stat gains (sum of two base classes)
HYBRID_GAINS = {
    ("order", "chaos"):   {**{k: CLASS_GAINS["order"].get(k, 0) + CLASS_GAINS["chaos"].get(k, 0) for k in set(CLASS_GAINS["order"]) | set(CLASS_GAINS["chaos"])}},
    ("order", "warrior"): {**{k: CLASS_GAINS["order"].get(k, 0) + CLASS_GAINS["warrior"].get(k, 0) for k in set(CLASS_GAINS["order"]) | set(CLASS_GAINS["warrior"])}},
    ("order", "mage"):    {**{k: CLASS_GAINS["order"].get(k, 0) + CLASS_GAINS["mage"].get(k, 0) for k in set(CLASS_GAINS["order"]) | set(CLASS_GAINS["mage"])}},
    ("chaos", "warrior"): {**{k: CLASS_GAINS["chaos"].get(k, 0) + CLASS_GAINS["warrior"].get(k, 0) for k in set(CLASS_GAINS["chaos"]) | set(CLASS_GAINS["warrior"])}},
    ("chaos", "mage"):    {**{k: CLASS_GAINS["chaos"].get(k, 0) + CLASS_GAINS["mage"].get(k, 0) for k in set(CLASS_GAINS["chaos"]) | set(CLASS_GAINS["mage"])}},
    ("warrior", "mage"):  {**{k: CLASS_GAINS["warrior"].get(k, 0) + CLASS_GAINS["mage"].get(k, 0) for k in set(CLASS_GAINS["warrior"]) | set(CLASS_GAINS["mage"])}},
}

# Map two-class combo → hybrid class name
HYBRID_CLASS_MAP = {
    frozenset(["order", "order"]):     "priest",
    frozenset(["order", "chaos"]):     "heretic",
    frozenset(["order", "warrior"]):   "paladin",
    frozenset(["order", "mage"]):      "prophet",
    frozenset(["chaos", "chaos"]):     "invoker",
    frozenset(["chaos", "warrior"]):   "rogue",
    frozenset(["chaos", "mage"]):      "sorcerer",
    frozenset(["warrior", "warrior"]): "knight",
    frozenset(["warrior", "mage"]):    "warlock",
    frozenset(["mage", "mage"]):       "wizard",
}

# XP needed to reach each level: Exp(L) = Exp(L-1) + 500 + 75*L + 20*L^2
def exp_needed_for_level(level: int) -> int:
    """Total XP needed to reach `level` from level 1."""
    total = 0
    for l in range(2, level + 1):
        total += 500 + 75 * l + 20 * l ** 2
    return total

# Enemy scaling: attack/defense/hp as function of level
def enemy_attack(level: int) -> int:
    return 5 + (level - 1) * 3

def enemy_defense(level: int) -> int:
    return 5 + (level - 1) * 2

def enemy_hp(level: int) -> int:
    return 100 + (level - 1) * 30

# Random hero names for recruitment pool
RANDOM_HERO_NAMES = [
    "Aldric", "Brina", "Cedric", "Dalia", "Edric",
    "Freya", "Gareth", "Hilda", "Ivan", "Jora",
    "Kael", "Lyra", "Magnus", "Nara", "Orion",
    "Petra", "Quinn", "Rena", "Silas", "Thea",
]
