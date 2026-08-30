from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LocationData:
    id: str
    name: str
    emoji: str
    description: str
    required_progress: str  # location that needs to be completed to unlock this one
    progress_threshold: int = 80  # % needed to unlock next location
    boss_unlock_threshold: int = 70  # % needed to unlock boss


LOCATIONS = {
    "forest": LocationData(
        id="forest",
        name="Лес",
        emoji="🌲",
        description="Стартовая локация. Дом для зайцев, лис и кабанов.",
        required_progress=None
    ),
    "taiga": LocationData(
        id="taiga",
        name="Тайга",
        emoji="🌨️",
        description="Хвойные леса с волками, рысями и лосями.",
        required_progress="forest",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "mountains": LocationData(
        id="mountains",
        name="Горы",
        emoji="⛰️",
        description="Высокие горы с горными козлами и барсами.",
        required_progress="taiga",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "steppe": LocationData(
        id="steppe",
        name="Степь",
        emoji="🏜️",
        description="Безграничные степи с антилопами, львами и гепардами.",
        required_progress="mountains",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "desert": LocationData(
        id="desert",
        name="Пустыня",
        emoji="🏜️",
        description="Жаркая пустыня с верблюдами, лисами и змеями.",
        required_progress="steppe",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "jungle": LocationData(
        id="jungle",
        name="Джунгли",
        emoji="🌴",
        description="Тропические джунгли с обезьянами, ягуарами и тиграми.",
        required_progress="desert",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "swamp": LocationData(
        id="swamp",
        name="Болото",
        emoji="🐸",
        description="Топкие болота с кабанами, аллигаторами и цаплями.",
        required_progress="jungle",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "tundra": LocationData(
        id="tundra",
        name="Тундра",
        emoji="❄️",
        description="Арктическая тундра с белыми медведями, песцами и моржами.",
        required_progress="swamp",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "savanna": LocationData(
        id="savanna",
        name="Саванна",
        emoji="🦒",
        description="Африканская саванна со слонами, жирафами и носорогами.",
        required_progress="tundra",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "rainforest": LocationData(
        id="rainforest",
        name="Тропический лес",
        emoji="🌴",
        description="Амазонские дождевые леса с экзотическими животными.",
        required_progress="savanna",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "north_forest": LocationData(
        id="north_forest",
        name="Северный лес",
        emoji="🌲",
        description="Суровые северные леса с крупными хищниками.",
        required_progress="rainforest",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "deep_forest": LocationData(
        id="deep_forest",
        name="Глухой лес",
        emoji="🌲",
        description="Тёмные чащи с древними и опасными обитателями.",
        required_progress="north_forest",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "ocean": LocationData(
        id="ocean",
        name="Океан",
        emoji="🌊",
        description="Бескрайний океан с рыбами, акулами и китами.",
        required_progress="deep_forest",
        progress_threshold=80,
        boss_unlock_threshold=70
    ),
    "volcano": LocationData(
        id="volcano",
        name="Вулкан",
        emoji="🌋",
        description="Опасный регион с огненными и магматическими существами.",
        required_progress="ocean",
        progress_threshold=80,
        boss_unlock_threshold=70
    )
}


def get_location(location_id: str) -> LocationData:
    return LOCATIONS.get(location_id)


def get_all_locations() -> List[LocationData]:
    return list(LOCATIONS.values())


def get_unlocked_locations(location_progress: Dict[str, float], game_mode: str = "free") -> List[LocationData]:
    """Get list of locations that are unlocked based on progress and game mode"""
    unlocked = []
    
    # In free mode, all locations are available
    if game_mode == "free":
        return list(LOCATIONS.values())
    
    # In story mode, locations unlock based on progress
    # Forest is always unlocked
    unlocked.append(LOCATIONS["forest"])
    
    # Check other locations
    for loc_id, location in LOCATIONS.items():
        if loc_id == "forest":
            continue
        
        if location.required_progress:
            required_progress = location_progress.get(location.required_progress, 0)
            if required_progress >= location.progress_threshold:
                unlocked.append(location)
    
    return unlocked


def can_unlock_location(location_id: str, location_progress: Dict[str, float], game_mode: str = "free") -> bool:
    """Check if a location can be unlocked"""
    location = LOCATIONS.get(location_id)
    if not location:
        return False
    
    # In free mode, all locations are accessible
    if game_mode == "free":
        return True
    
    # In story mode, check progress requirements
    if location.required_progress is None:
        return True  # Starting location
    
    required_progress = location_progress.get(location.required_progress, 0)
    return required_progress >= location.progress_threshold


def is_boss_unlocked(location_id: str, location_progress: Dict[str, float]) -> bool:
    """Check if boss is unlocked for a location"""
    location = LOCATIONS.get(location_id)
    if not location:
        return False
    
    progress = location_progress.get(location_id, 0)
    return progress >= location.boss_unlock_threshold


def get_location_order() -> List[str]:
    """Get the order in which locations should be unlocked"""
    return ["forest", "taiga", "mountains", "steppe", "desert", "jungle", "swamp", "tundra", "savanna", "rainforest", "north_forest", "deep_forest", "ocean", "volcano"]
