import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logic

def test_calculate_xp_required():
    """Test the recursive XP formula."""
    assert logic.calculate_xp_required(1) == 0
    
    assert logic.calculate_xp_required(2) == 730

def test_determine_classes_base():
    """Test a hero with no level 5 classes."""
    class_levels = {"Order": 3, "Chaos": 0, "Warrior": 0, "Mage": 0}
    is_hybrid, hybrid_name, specialization = logic.determine_classes(class_levels)
    
    assert is_hybrid is False
    assert hybrid_name is None
    assert specialization is None

def test_determine_classes_specialization():
    """Test a hero that reached level 5 in one class."""
    class_levels = {"Order": 5, "Chaos": 2, "Warrior": 0, "Mage": 0}
    is_hybrid, hybrid_name, specialization = logic.determine_classes(class_levels)
    
    assert is_hybrid is False
    assert hybrid_name is None
    assert specialization == "Order"

def test_determine_classes_hybrid():
    """Test a hero that reached level 5 in two classes."""
    class_levels = {"Order": 5, "Chaos": 0, "Warrior": 5, "Mage": 0}
    is_hybrid, hybrid_name, specialization = logic.determine_classes(class_levels)
    
    assert is_hybrid is True
    assert hybrid_name == "Paladin"
    assert specialization is None

def test_calculate_stats_base_growth():
    """Test that base stats increment correctly before class bonuses."""
    hero_record = {
        "total_level": 2,
        "class_levels": {"Order": 0, "Chaos": 0, "Warrior": 0, "Mage": 0}
    }
    stats_data = logic.calculate_stats(hero_record)
    
    assert stats_data["max_stats"]["attack"] == 5 + 1
    assert stats_data["max_stats"]["defense"] == 5 + 1
    assert stats_data["max_stats"]["hp"] == 100 + 5
    assert stats_data["max_stats"]["mana"] == 50 + 2

def test_get_abilities_base_classes():
    """Test that base classes grant their standard abilities."""
    class_levels = {"Order": 1, "Chaos": 1, "Warrior": 0, "Mage": 0}
    abilities = logic.get_abilities(class_levels, None)
    
    ability_names = [ab["name"] for ab in abilities]
    assert "Protect" in ability_names
    assert "Heal" in ability_names
    assert "Fireball" in ability_names
    assert "Chain Lightning" in ability_names
    assert "Berserker Attack" not in ability_names

def test_get_abilities_hybrid_priest():
    """Test the Priest hybrid modifier (Order + Order specialization)."""
    class_levels = {"Order": 5, "Chaos": 0, "Warrior": 0, "Mage": 0}
    abilities = logic.get_abilities(class_levels, "Priest")
    
    ability_names = [ab["name"] for ab in abilities]
    assert "Heal" not in ability_names
    assert "Group Heal" in ability_names
    
    group_heal = next(ab for ab in abilities if ab["name"] == "Group Heal")
    assert group_heal["effect_modifier"] == "Heal now applies to all friendly units"

def test_get_abilities_hybrid_heretic():
    """Test the Heretic hybrid modifier (Order + Chaos)."""
    class_levels = {"Order": 5, "Chaos": 5, "Warrior": 0, "Mage": 0}
    abilities = logic.get_abilities(class_levels, "Heretic")
    
    ability_names = [ab["name"] for ab in abilities]
    assert "Protect" not in ability_names
    assert "Fire Shield" in ability_names
    
    fire_shield = next(ab for ab in abilities if ab["name"] == "Fire Shield")
    assert fire_shield["mana_cost"] == 25
    assert fire_shield["effect_modifier"] == "Returns 10% of damage back to attacker"

def test_get_abilities_hybrid_rogue():
    """Test the Rogue hybrid passive addition (Chaos + Warrior)."""
    class_levels = {"Order": 0, "Chaos": 5, "Warrior": 5, "Mage": 0}
    abilities = logic.get_abilities(class_levels, "Rogue")
    
    ability_names = [ab["name"] for ab in abilities]
    assert "Sneak Attack" in ability_names
    
    sneak_attack = next(ab for ab in abilities if ab["name"] == "Sneak Attack")
    assert sneak_attack["type"] == "passive"
    assert sneak_attack["mana_cost"] == 0

def test_get_abilities_hybrid_wizard():
    """Test the Wizard hybrid modifier (Mage + Mage specialization)."""
    class_levels = {"Order": 0, "Chaos": 0, "Warrior": 0, "Mage": 5}
    abilities = logic.get_abilities(class_levels, "Wizard")
    
    replenish = next(ab for ab in abilities if ab["name"] == "Replenish")
    assert replenish["mana_cost"] == 40
    assert replenish["effect_modifier"] == "Cost reduced to 40 mana"