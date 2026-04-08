"""
battle.py - The PvP Battle Engine
-----------------------------------
This file handles all the fighting logic.
It follows the rules from the project spec:
  - Units act in order of level (highest first), teams alternate
  - Actions: attack, defend, cast special ability
  - Damage = attacker's attack - defender's defense
  - Shields absorb damage before HP
  - Defend: skip turn, gain +10 HP and +5 mana
  - Battle ends when one whole team reaches 0 HP
  - No exp or gold changes in PvP
"""

import random


# -------------------------------------------------------
# Hero class
# -------------------------------------------------------

class Hero:
    """Represents one hero in battle."""

    def __init__(self, data):
        self.name       = data.get("name", "Unknown")
        self.level      = int(data.get("level", 1))
        self.attack     = int(data.get("attack", 5))
        self.defense    = int(data.get("defense", 5))
        self.hp         = int(data.get("hp", 100))
        self.max_hp     = int(data.get("max_hp", self.hp))
        self.mana       = int(data.get("mana", 50))
        self.max_mana   = int(data.get("max_mana", self.mana))
        self.shield     = int(data.get("shield", 0))
        self.class_name = data.get("class_name", "Warrior")
        self.stunned    = False

    @property
    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        """Apply damage. Shield absorbs first, then HP takes the rest."""
        if amount <= 0:
            return 0
        if self.shield > 0:
            absorbed = min(self.shield, amount)
            self.shield -= absorbed
            amount -= absorbed
        actual = min(amount, self.hp)
        self.hp -= actual
        return actual

    def restore_hp(self, amount):
        """Heal the hero, but not above max_hp."""
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def restore_mana(self, amount):
        """Restore mana, but not above max_mana."""
        before = self.mana
        self.mana = min(self.max_mana, self.mana + amount)
        return self.mana - before

    def to_dict(self):
        """Convert back to a plain dictionary to send in the API response."""
        return {
            "name": self.name,
            "level": self.level,
            "attack": self.attack,
            "defense": self.defense,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "shield": self.shield,
            "class_name": self.class_name
        }


# -------------------------------------------------------
# Special ability mana costs and defaults per class
# -------------------------------------------------------

ABILITY_MANA_COST = {
    "protect":          25,
    "heal":             35,
    "fireball":         30,
    "chain_lightning":  40,
    "berserker_attack": 60,
    "replenish":        80,
}

DEFAULT_ABILITY = {
    "Order":   "protect",
    "Chaos":   "fireball",
    "Warrior": "berserker_attack",
    "Mage":    "replenish",
    "Priest":  "heal",
    "Knight":  "berserker_attack",
    "Warlock": "berserker_attack",
    "Wizard":  "replenish",
}


def get_ability(hero):
    """Return the special ability name for a hero based on their class (case-insensitive)."""
    class_name = hero.class_name if isinstance(hero.class_name, str) else "Warrior"
    # Try exact match first, then title-cased
    return DEFAULT_ABILITY.get(class_name) or DEFAULT_ABILITY.get(class_name.title(), "berserker_attack")


# -------------------------------------------------------
# Special ability implementations
# -------------------------------------------------------

def cast_protect(caster, allies, log):
    """Order: Apply a shield to all allies equal to 10% of their max HP."""
    for ally in allies:
        shield_val = max(1, int(ally.max_hp * 0.10))
        ally.shield = shield_val
        log.append(f"    {ally.name} gets a shield of {shield_val}.")


def cast_heal(caster, allies, log):
    """Order: Heal the ally with the lowest HP for 25% of their max HP."""
    target = min(allies, key=lambda h: h.hp)
    amount = max(1, int(target.max_hp * 0.25))
    healed = target.restore_hp(amount)
    log.append(f"    {target.name} is healed for {healed} HP. (HP: {target.hp}/{target.max_hp})")


def cast_fireball(caster, enemies, log):
    """Chaos: Hit up to 3 random enemies with a fire attack."""
    targets = random.sample(enemies, min(3, len(enemies)))
    for t in targets:
        dmg = max(0, caster.attack - t.defense)
        actual = t.take_damage(dmg)
        log.append(f"    Fireball hits {t.name} for {actual} damage. (HP: {t.hp}/{t.max_hp})")
        if not t.is_alive:
            log.append(f"    {t.name} is defeated!")


def cast_chain_lightning(caster, enemies, log):
    """Chaos: Hit all enemies. First takes full damage, each next takes 25% of the previous."""
    first = random.choice(enemies)
    rest = [e for e in enemies if e is not first]
    random.shuffle(rest)
    chain = [first] + rest

    current_dmg = max(0, caster.attack - first.defense)
    for i, target in enumerate(chain):
        if i > 0:
            current_dmg = max(0, int(current_dmg * 0.25))
        if current_dmg == 0:
            break
        actual = target.take_damage(current_dmg)
        log.append(f"    Chain Lightning hits {target.name} for {actual}. (HP: {target.hp}/{target.max_hp})")
        if not target.is_alive:
            log.append(f"    {target.name} is defeated!")


def cast_berserker_attack(caster, enemies, log):
    """Warrior: Attack the main target, then splash 2 more enemies for 25% damage."""
    main_target = min(enemies, key=lambda h: h.hp)
    main_dmg = max(0, caster.attack - main_target.defense)
    actual = main_target.take_damage(main_dmg)
    log.append(f"    Berserker Attack hits {main_target.name} for {actual}. (HP: {main_target.hp}/{main_target.max_hp})")
    if not main_target.is_alive:
        log.append(f"    {main_target.name} is defeated!")

    others = [e for e in enemies if e is not main_target and e.is_alive]
    for splash_target in random.sample(others, min(2, len(others))):
        splash_dmg = max(0, int(main_dmg * 0.25))
        splash_actual = splash_target.take_damage(splash_dmg)
        log.append(f"    Splash hits {splash_target.name} for {splash_actual}. (HP: {splash_target.hp}/{splash_target.max_hp})")
        if not splash_target.is_alive:
            log.append(f"    {splash_target.name} is defeated!")


def cast_replenish(caster, allies, log):
    """Mage: Restore 30 mana to all allies, and 60 to self."""
    for ally in allies:
        amount = 60 if ally is caster else 30
        gained = ally.restore_mana(amount)
        log.append(f"    {ally.name} restores {gained} mana. (mana: {ally.mana}/{ally.max_mana})")


def use_special_ability(hero, allies, enemies, log):
    """Figure out which ability to cast and call the right function."""
    ability = get_ability(hero)
    cost = ABILITY_MANA_COST.get(ability, 999)

    if hero.mana < cost:
        log.append(f"  {hero.name} doesn't have enough mana for {ability}. Attacks instead.")
        do_basic_attack(hero, enemies, log)
        return

    hero.mana -= cost
    log.append(f"  {hero.name} casts {ability}!")

    if ability == "protect":
        cast_protect(hero, allies, log)
    elif ability == "heal":
        cast_heal(hero, allies, log)
    elif ability == "fireball":
        cast_fireball(hero, enemies, log)
    elif ability == "chain_lightning":
        cast_chain_lightning(hero, enemies, log)
    elif ability == "berserker_attack":
        cast_berserker_attack(hero, enemies, log)
    elif ability == "replenish":
        cast_replenish(hero, allies, log)


# -------------------------------------------------------
# Basic actions
# -------------------------------------------------------

def do_basic_attack(attacker, enemies, log):
    """Attack the enemy with the lowest HP. Damage = attacker.attack - target.defense."""
    target = min(enemies, key=lambda h: h.hp)
    dmg = max(0, attacker.attack - target.defense)
    actual = target.take_damage(dmg)
    log.append(f"  {attacker.name} attacks {target.name} for {actual} damage. "
               f"(HP: {target.hp}/{target.max_hp})")
    if not target.is_alive:
        log.append(f"  {target.name} is defeated!")


def do_defend(hero, log):
    """Skip turn, regain +10 HP and +5 mana."""
    hp_gained = hero.restore_hp(10)
    mana_gained = hero.restore_mana(5)
    log.append(f"  {hero.name} defends! (+{hp_gained} HP, +{mana_gained} mana)")


# -------------------------------------------------------
# AI action choice
# -------------------------------------------------------

def choose_action(hero, allies, enemies):
    """Decide what the hero does this turn."""
    ability = get_ability(hero)
    cost = ABILITY_MANA_COST.get(ability, 999)

    # Use healing/support spells if someone is hurt
    if ability in ("heal", "protect", "replenish") and hero.mana >= cost:
        if any(h.hp < h.max_hp * 0.6 for h in allies):
            return "cast"

    # Use offensive spells if there are multiple enemies
    if ability in ("fireball", "chain_lightning", "berserker_attack") and hero.mana >= cost:
        if len(enemies) > 1:
            return "cast"

    # Defend if HP is very low
    if hero.hp < hero.max_hp * 0.25:
        return "defend"

    return "attack"


# -------------------------------------------------------
# Main battle function
# -------------------------------------------------------

def run_battle(inviter_party_data, invitee_party_data, inviter_name, invitee_name):
    """
    Run the full battle between two parties.
    Returns a dict with the winner, log, and final party states.
    """
    team_a = [Hero(h) for h in inviter_party_data]
    team_b = [Hero(h) for h in invitee_party_data]

    log = []
    log.append(f"=== {inviter_name} vs {invitee_name} ===")

    round_number = 0
    max_rounds = 100  # safety limit so the battle can't go on forever

    while round_number < max_rounds:
        if not any(h.is_alive for h in team_a):
            break
        if not any(h.is_alive for h in team_b):
            break

        round_number += 1
        log.append(f"\n--- Round {round_number} ---")

        # Sort each team by level, highest first
        alive_a = sorted([h for h in team_a if h.is_alive], key=lambda h: h.level, reverse=True)
        alive_b = sorted([h for h in team_b if h.is_alive], key=lambda h: h.level, reverse=True)

        # The team with the highest level unit goes first
        top_a_level = alive_a[0].level if alive_a else 0
        top_b_level = alive_b[0].level if alive_b else 0

        if top_a_level >= top_b_level:
            first_team, second_team = alive_a, alive_b
            first_enemies  = lambda: [h for h in team_b if h.is_alive]
            second_enemies = lambda: [h for h in team_a if h.is_alive]
            first_allies   = lambda: [h for h in team_a if h.is_alive]
            second_allies  = lambda: [h for h in team_b if h.is_alive]
        else:
            first_team, second_team = alive_b, alive_a
            first_enemies  = lambda: [h for h in team_a if h.is_alive]
            second_enemies = lambda: [h for h in team_b if h.is_alive]
            first_allies   = lambda: [h for h in team_b if h.is_alive]
            second_allies  = lambda: [h for h in team_a if h.is_alive]

        # Interleave turns: first[0], second[0], first[1], second[1], ...
        turns = []
        for i in range(max(len(first_team), len(second_team))):
            if i < len(first_team):
                turns.append((first_team[i], first_enemies, first_allies))
            if i < len(second_team):
                turns.append((second_team[i], second_enemies, second_allies))

        for hero, get_enemies, get_allies in turns:
            if not hero.is_alive:
                continue

            enemies = get_enemies()
            allies  = get_allies()

            if not enemies:
                break

            if hero.stunned:
                log.append(f"  {hero.name} is stunned and loses their turn!")
                hero.stunned = False
                continue

            action = choose_action(hero, allies, enemies)

            if action == "cast":
                use_special_ability(hero, allies, enemies, log)
            elif action == "defend":
                do_defend(hero, log)
            else:
                do_basic_attack(hero, enemies, log)

    # Determine the winner
    a_alive = any(h.is_alive for h in team_a)
    b_alive = any(h.is_alive for h in team_b)

    if a_alive and not b_alive:
        winner = "inviter"
        log.append(f"\n=== {inviter_name} wins! ===")
    elif b_alive and not a_alive:
        winner = "invitee"
        log.append(f"\n=== {invitee_name} wins! ===")
    else:
        winner = "draw"
        log.append("\n=== It's a draw! ===")

    return {
        "winner": winner,
        "log": log,
        "inviter_party": [h.to_dict() for h in team_a],
        "invitee_party": [h.to_dict() for h in team_b],
    }