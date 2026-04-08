# Constants for Base Stats and Growth
BASE_STATS = {"attack": 5, "defense": 5, "hp": 100, "mana": 50}
BASE_GROWTH = {"attack": 1, "defense": 1, "hp": 5, "mana": 2}

# Class Specific Growths
CLASS_GROWTH = {
    "Order": {"attack": 0, "defense": 2, "hp": 0, "mana": 5},
    "Chaos": {"attack": 3, "defense": 0, "hp": 5, "mana": 0},
    "Warrior": {"attack": 2, "defense": 3, "hp": 0, "mana": 0},
    "Mage": {"attack": 1, "defense": 0, "hp": 0, "mana": 5}
}

# Hybrid Class Mapping Table
HYBRID_MATRIX = {
    ("Order", "Order"): "Priest", ("Order", "Chaos"): "Heretic", 
    ("Order", "Warrior"): "Paladin", ("Order", "Mage"): "Prophet",
    ("Chaos", "Chaos"): "Invoker", ("Chaos", "Warrior"): "Rogue", 
    ("Chaos", "Mage"): "Sorcerer",
    ("Warrior", "Warrior"): "Knight", ("Warrior", "Mage"): "Warlock",
    ("Mage", "Mage"): "Wizard"
}

def calculate_xp_required(level):
    """Calculates total XP required to reach a specific level recursively."""
    if level <= 1:
        return 0
    return calculate_xp_required(level - 1) + 500 + (75 * level) + (20 * (level ** 2))

def determine_classes(class_levels):
    """Determines if the hero has a specialization or a hybrid class."""
    classes_at_5 = [cls for cls, lvl in class_levels.items() if lvl >= 5]
    
    is_hybrid = len(classes_at_5) >= 2
    hybrid_name = None
    specialization = None

    if is_hybrid:
        combo = tuple(sorted(classes_at_5[:2], key=lambda x: ["Order", "Chaos", "Warrior", "Mage"].index(x)))
        hybrid_name = HYBRID_MATRIX.get(combo)
    elif len(classes_at_5) == 1:
        specialization = classes_at_5[0]

    return is_hybrid, hybrid_name, specialization

def calculate_stats(hero_record):
    """Dynamically calculates maximum stats based on levels and hybrid rules."""
    stats = BASE_STATS.copy()
    total_level = hero_record['total_level']
    class_levels = hero_record['class_levels']

    levels_gained = total_level - 1
    for stat in stats:
        stats[stat] += BASE_GROWTH[stat] * levels_gained

    is_hybrid, hybrid_name, specialization = determine_classes(class_levels)

    for cls, lvl in class_levels.items():
        if lvl == 0:
            continue
            
        multiplier = 1
        if not is_hybrid and specialization == cls:
            multiplier = 2 

        for stat, value in CLASS_GROWTH[cls].items():
            stats[stat] += (value * lvl * multiplier)

    return {
        "max_stats": stats,
        "is_hybrid": is_hybrid,
        "hybrid_class": hybrid_name,
        "specialization": specialization if not is_hybrid else None
    }

def get_abilities(class_levels, hybrid_name):
    """Returns a list of abilities the hero has unlocked based on their classes/hybrid."""
    abilities = []

    if class_levels.get("Order", 0) > 0:
        abilities.extend([
            {"name": "Protect", "mana_cost": 25, "type": "spell"}, 
            {"name": "Heal", "mana_cost": 35, "type": "spell"}
        ])
    if class_levels.get("Chaos", 0) > 0:
        abilities.extend([
            {"name": "Fireball", "mana_cost": 30, "type": "spell"}, 
            {"name": "Chain Lightning", "mana_cost": 40, "type": "spell"}
        ])
    if class_levels.get("Warrior", 0) > 0:
        abilities.append({"name": "Berserker Attack", "mana_cost": 60, "type": "special"})
    if class_levels.get("Mage", 0) > 0:
        abilities.append({"name": "Replenish", "mana_cost": 80, "type": "spell"})

    if hybrid_name == "Priest":
        for ab in abilities:
            if ab["name"] == "Heal":
                ab["name"] = "Group Heal"
                ab["effect_modifier"] = "Heal now applies to all friendly units"

    elif hybrid_name == "Heretic":
        abilities = [ab for ab in abilities if ab["name"] != "Protect"]
        abilities.append({
            "name": "Fire Shield", 
            "mana_cost": 25, 
            "type": "spell", 
            "effect_modifier": "Returns 10% of damage back to attacker"
        })

    elif hybrid_name == "Paladin":
        for ab in abilities:
            if ab["name"] == "Berserker Attack":
                ab["effect_modifier"] = "Heals Paladin for 10% of original HP before attacking"

    elif hybrid_name == "Prophet":
        for ab in abilities:
            if ab["name"] in ["Protect", "Heal", "Replenish"]:
                ab["effect_modifier"] = "Double effect"

    elif hybrid_name == "Invoker":
        for ab in abilities:
            if ab["name"] == "Chain Lightning":
                ab["effect_modifier"] = "Does 50% damage for every subsequent target hit"

    elif hybrid_name == "Rogue":
        abilities.append({
            "name": "Sneak Attack", 
            "mana_cost": 0, 
            "type": "passive", 
            "effect_modifier": "50% chance for an additional attack for 50% total damage"
        })

    elif hybrid_name == "Sorcerer":
        for ab in abilities:
            if ab["name"] == "Fireball":
                ab["effect_modifier"] = "Causes double damage to all affected units"

    elif hybrid_name == "Knight":
        for ab in abilities:
            if ab["name"] == "Berserker Attack":
                ab["effect_modifier"] = "50% chance of stunning the units hit"

    elif hybrid_name == "Warlock":
        abilities.append({
            "name": "Mana Burn", 
            "mana_cost": 0, 
            "type": "passive", 
            "effect_modifier": "Burns 10% of target's total mana points on attack"
        })

    elif hybrid_name == "Wizard":
        for ab in abilities:
            if ab["name"] == "Replenish":
                ab["mana_cost"] = 40
                ab["effect_modifier"] = "Cost reduced to 40 mana"

    return abilities