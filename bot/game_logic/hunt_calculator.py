from bot.config import BASE_ACCURACY, MAX_ACCURACY
from bot.game_logic.animals import AnimalData


def calculate_hit_chance(
    accuracy_skill: int,
    weapon_type: str,
    weapon_durability: int,
    track_buff: bool = False,
    track_bonus: int = 0,
    ambush_buff: bool = False,
    weather: str = "clear"
) -> int:
    """
    Calculate hit chance based on various factors.

    Args:
        accuracy_skill: Player's accuracy skill level (0-15)
        weapon_type: Type of weapon (bow, crossbow, rifle, shotgun)
        weapon_durability: Current weapon durability (0-100)
        track_buff: Whether track buff is active
        track_bonus: Bonus from track buff (-5 to 20)
        ambush_buff: Whether ambush buff is active
        weather: Current weather (clear, rain, fog, snow)

    Returns:
        Hit chance as percentage (0-100)
    """
    chance = BASE_ACCURACY

    # Skill bonus (+2% per level, max +30%)
    skill_bonus = min(accuracy_skill * 2, 30)
    chance += skill_bonus

    # Weapon bonus
    weapon_bonus = {
        "bow": 0,
        "crossbow": 5,
        "rifle": 10,
        "shotgun": -5  # Penalty at range, bonus at close range (simplified)
    }
    chance += weapon_bonus.get(weapon_type, 0)

    # Durability penalty
    if weapon_durability < 50:
        chance -= 10

    # Buffs
    if track_buff:
        chance += track_bonus
    if ambush_buff:
        chance += 5

    # Weather penalty
    weather_penalty = {
        "clear": 0,
        "rain": -10,
        "fog": -10,
        "snow": -10
    }
    chance += weather_penalty.get(weather, 0)

    # Cap at maximum
    chance = min(chance, MAX_ACCURACY)

    # Ensure minimum
    chance = max(chance, 5)

    return int(chance)


def calculate_energy_cost(action: str, endurance_skill: int = 0) -> int:
    """
    Calculate energy cost for an action based on endurance skill.
    
    Args:
        action: Type of action (hunt, track, bait, ambush, travel)
        endurance_skill: Player's endurance skill level (0-50)
    
    Returns:
        Energy cost
    """
    base_costs = {
        "hunt": 5,
        "track": 3,
        "bait": 4,
        "ambush": 6,
        "travel": 5
    }
    
    base_cost = base_costs.get(action, 5)
    
    # Endurance reduces cost by 1% per level (minimum 1 energy)
    reduction_percent = min(endurance_skill, 50)
    cost = int(base_cost * (1 - reduction_percent / 100))
    cost = max(cost, 1)
    
    return cost


def calculate_max_energy(endurance_skill: int = 0) -> int:
    """
    Calculate max energy based on endurance skill.
    
    Args:
        endurance_skill: Player's endurance skill level (0-50)
    
    Returns:
        Maximum energy
    """
    from bot.config import MAX_ENERGY
    return MAX_ENERGY + (endurance_skill * 2)
