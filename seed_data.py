import asyncio
from bot.database.db import async_session, init_db
from bot.database.models import Animal, Quest
from bot.game_logic.animals import ANIMALS_BY_LOCATION


QUESTS_DATA = [
    # Forest quests - Лес
    {
        "title": "Первая добыча",
        "description": "Убейте зайца и принесите его шкуру.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 1,
        "reward_exp": 50,
        "reward_coins": 25,
        "conditions": {"kill": {"animal": "Заяц", "count": 1}},
        "progress_reward": 10
    },
    {
        "title": "Хитрая лиса",
        "description": "Убейте 3 лис.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 2,
        "reward_exp": 100,
        "reward_coins": 75,
        "conditions": {"kill": {"animal": "Лиса", "count": 3}},
        "progress_reward": 12
    },
    {
        "title": "Кабанья напасть",
        "description": "Убейте 5 кабанов.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 3,
        "reward_exp": 150,
        "reward_coins": 100,
        "conditions": {"kill": {"animal": "Кабан", "count": 5}},
        "progress_reward": 12
    },
    {
        "title": "Таинственный след",
        "description": "Исследуйте локацию.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 4,
        "reward_exp": 80,
        "reward_coins": 50,
        "conditions": {"explore": {"location": "forest", "count": 1}},
        "progress_reward": 10
    },
    {
        "title": "Логово кабана",
        "description": "Убейте 10 кабанов вокруг логова.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 5,
        "reward_exp": 200,
        "reward_coins": 150,
        "conditions": {"kill": {"animal": "Кабан", "count": 10}},
        "progress_reward": 15
    },
    {
        "title": "Оленьи рога",
        "description": "Убейте 5 оленей.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 6,
        "reward_exp": 250,
        "reward_coins": 180,
        "conditions": {"kill": {"animal": "Олень", "count": 5}},
        "progress_reward": 12
    },
    {
        "title": "Волчья стая",
        "description": "Убейте 8 волков.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 7,
        "reward_exp": 300,
        "reward_coins": 220,
        "conditions": {"kill": {"animal": "Волк", "count": 8}},
        "progress_reward": 14
    },
    {
        "title": "Лосиный трофей",
        "description": "Убейте 3 лосей.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 8,
        "reward_exp": 350,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Лось", "count": 3}},
        "progress_reward": 15
    },
    {
        "title": "Зубровая охота",
        "description": "Убейте 2 зубров.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 9,
        "reward_exp": 400,
        "reward_coins": 300,
        "conditions": {"kill": {"animal": "Зубр", "count": 2}},
        "progress_reward": 16
    },
    {
        "title": "Медвежий лес",
        "description": "Убейте 2 медведей.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 10,
        "reward_exp": 450,
        "reward_coins": 340,
        "conditions": {"kill": {"animal": "Медведь", "count": 2}},
        "progress_reward": 18
    },
    {
        "title": "Призрачный олень",
        "description": "Убейте легендарного призрачного оленя.",
        "quest_type": "main",
        "location": "forest",
        "required_level": 12,
        "reward_exp": 800,
        "reward_coins": 600,
        "conditions": {"kill": {"animal": "Призрачный олень", "count": 1}},
        "progress_reward": 20,
        "is_boss_quest": True,
        "boss_name": "Призрачный олень"
    },
    # Side quests for forest
    {
        "title": "Охота на зайцев",
        "description": "Убейте 10 зайцев.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 1,
        "reward_exp": 30,
        "reward_coins": 20,
        "conditions": {"kill": {"animal": "Заяц", "count": 10}},
        "progress_reward": 3,
        "is_repeatable": True
    },
    {
        "title": "Лисий воротник",
        "description": "Принесите 5 лисьих шкур.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 2,
        "reward_exp": 50,
        "reward_coins": 40,
        "conditions": {"collect": {"item": "шкура лисы", "count": 5}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Кабаний корм",
        "description": "Принесите 10 кабаньих шкур.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 3,
        "reward_exp": 60,
        "reward_coins": 50,
        "conditions": {"collect": {"item": "шкура кабана", "count": 10}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Оленьи шкуры",
        "description": "Принесите 8 оленьих шкур.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 6,
        "reward_exp": 80,
        "reward_coins": 70,
        "conditions": {"collect": {"item": "шкура оленя", "count": 8}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Волчьи клыки",
        "description": "Принесите 12 волчьих клыков.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 7,
        "reward_exp": 90,
        "reward_coins": 80,
        "conditions": {"collect": {"item": "клык волка", "count": 12}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Медвежьи когти",
        "description": "Принесите 6 медвежьих когтей.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 10,
        "reward_exp": 110,
        "reward_coins": 100,
        "conditions": {"collect": {"item": "коготь медведя", "count": 6}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Охота на кабанов",
        "description": "Убейте 15 кабанов.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 5,
        "reward_exp": 70,
        "reward_coins": 60,
        "conditions": {"kill": {"animal": "Кабан", "count": 15}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    # Taiga quests - Тайга
    {
        "title": "Тайный след",
        "description": "Убейте 5 зайцев-беляков.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 8,
        "reward_exp": 200,
        "reward_coins": 150,
        "conditions": {"kill": {"animal": "Заяц-беляк", "count": 5}},
        "progress_reward": 10
    },
    {
        "title": "Волчий бич",
        "description": "Убейте 10 волков.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 9,
        "reward_exp": 250,
        "reward_coins": 200,
        "conditions": {"kill": {"animal": "Волк", "count": 10}},
        "progress_reward": 12
    },
    {
        "title": "Соболиная охота",
        "description": "Убейте 8 соболей.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 10,
        "reward_exp": 300,
        "reward_coins": 240,
        "conditions": {"kill": {"animal": "Соболь", "count": 8}},
        "progress_reward": 13
    },
    {
        "title": "Росомаха",
        "description": "Убейте 5 росомах.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 11,
        "reward_exp": 350,
        "reward_coins": 280,
        "conditions": {"kill": {"animal": "Росомаха", "count": 5}},
        "progress_reward": 14
    },
    {
        "title": "Рыси тайги",
        "description": "Убейте 6 рысей.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 12,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Рысь", "count": 6}},
        "progress_reward": 15
    },
    {
        "title": "Кабанья тайга",
        "description": "Убейте 7 кабанов.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 13,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Кабан", "count": 7}},
        "progress_reward": 16
    },
    {
        "title": "Северный олень",
        "description": "Убейте 4 северных оленей.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 14,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Северный олень", "count": 4}},
        "progress_reward": 17
    },
    {
        "title": "Лось тайги",
        "description": "Убейте 3 лосей.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 15,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Лось", "count": 3}},
        "progress_reward": 18
    },
    {
        "title": "Медведь тайги",
        "description": "Убейте 2 медведей.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 16,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Медведь", "count": 2}},
        "progress_reward": 19
    },
    {
        "title": "Амурский тигр",
        "description": "Убейте амурского тигра.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 17,
        "reward_exp": 700,
        "reward_coins": 550,
        "conditions": {"kill": {"animal": "Амурский тигр", "count": 1}},
        "progress_reward": 20
    },
    {
        "title": "Дух тайги",
        "description": "Убейте легендарного духа тайги.",
        "quest_type": "main",
        "location": "taiga",
        "required_level": 18,
        "reward_exp": 1000,
        "reward_coins": 800,
        "conditions": {"kill": {"animal": "Дух тайги", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Дух тайги"
    },
    # Side quests for taiga
    {
        "title": "Охота на зайцев-беляков",
        "description": "Убейте 15 зайцев-беляков.",
        "quest_type": "side",
        "location": "taiga",
        "required_level": 8,
        "reward_exp": 70,
        "reward_coins": 60,
        "conditions": {"kill": {"animal": "Заяц-беляк", "count": 15}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Соболиные шкуры",
        "description": "Принесите 10 соболиных шкур.",
        "quest_type": "side",
        "location": "taiga",
        "required_level": 10,
        "reward_exp": 90,
        "reward_coins": 80,
        "conditions": {"collect": {"item": "шкура соболя", "count": 10}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Волчья шкура",
        "description": "Принесите 8 волчьих шкур.",
        "quest_type": "side",
        "location": "taiga",
        "required_level": 9,
        "reward_exp": 80,
        "reward_coins": 70,
        "conditions": {"collect": {"item": "шкура волка", "count": 8}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Рысьи когти",
        "description": "Принесите 9 рысьих когтей.",
        "quest_type": "side",
        "location": "taiga",
        "required_level": 12,
        "reward_exp": 100,
        "reward_coins": 90,
        "conditions": {"collect": {"item": "коготь рыси", "count": 9}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Медвежьи когти",
        "description": "Принесите 7 медвежьих когтей.",
        "quest_type": "side",
        "location": "taiga",
        "required_level": 16,
        "reward_exp": 120,
        "reward_coins": 110,
        "conditions": {"collect": {"item": "коготь медведя", "count": 7}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Mountains quests - Горы
    {
        "title": "Горный козёл",
        "description": "Убейте 8 горных козлов.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 12,
        "reward_exp": 280,
        "reward_coins": 220,
        "conditions": {"kill": {"animal": "Горный козёл", "count": 8}},
        "progress_reward": 12
    },
    {
        "title": "Сурки",
        "description": "Убейте 10 сурков.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 13,
        "reward_exp": 300,
        "reward_coins": 240,
        "conditions": {"kill": {"animal": "Сурок", "count": 10}},
        "progress_reward": 13
    },
    {
        "title": "Беркут",
        "description": "Убейте 5 беркутов.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 14,
        "reward_exp": 350,
        "reward_coins": 280,
        "conditions": {"kill": {"animal": "Беркут", "count": 5}},
        "progress_reward": 14
    },
    {
        "title": "Горный баран",
        "description": "Убейте 6 горных баранов.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 15,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Горный баран", "count": 6}},
        "progress_reward": 15
    },
    {
        "title": "Як",
        "description": "Убейте 4 яков.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 16,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Як", "count": 4}},
        "progress_reward": 16
    },
    {
        "title": "Снежный барс",
        "description": "Убейте 3 снежных барсов.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 17,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Снежный барс", "count": 3}},
        "progress_reward": 17
    },
    {
        "title": "Пума",
        "description": "Убейте 4 пум.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 18,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Пума", "count": 4}},
        "progress_reward": 18
    },
    {
        "title": "Горный орёл",
        "description": "Убейте 3 горных орлов.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 19,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Горный орёл", "count": 3}},
        "progress_reward": 19
    },
    {
        "title": "Медведь гризли",
        "description": "Убейте 2 медведей гризли.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 20,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Медведь гризли", "count": 2}},
        "progress_reward": 20
    },
    {
        "title": "Горный лев",
        "description": "Убейте горного льва.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 21,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Горный лев", "count": 1}},
        "progress_reward": 21
    },
    {
        "title": "Властелин гор",
        "description": "Убейте легендарного властелина гор.",
        "quest_type": "main",
        "location": "mountains",
        "required_level": 22,
        "reward_exp": 1100,
        "reward_coins": 900,
        "conditions": {"kill": {"animal": "Властелин гор", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Властелин гор"
    },
    # Side quests for mountains
    {
        "title": "Горные трофеи",
        "description": "Принесите 6 рогов горного козла.",
        "quest_type": "side",
        "location": "mountains",
        "required_level": 12,
        "reward_exp": 100,
        "reward_coins": 90,
        "conditions": {"collect": {"item": "рог козла", "count": 6}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Орлиные перья",
        "description": "Принесите 8 орлиных перьев.",
        "quest_type": "side",
        "location": "mountains",
        "required_level": 14,
        "reward_exp": 110,
        "reward_coins": 100,
        "conditions": {"collect": {"item": "перо орла", "count": 8}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Барсийи когти",
        "description": "Принесите 7 барсьих когтей.",
        "quest_type": "side",
        "location": "mountains",
        "required_level": 17,
        "reward_exp": 130,
        "reward_coins": 120,
        "conditions": {"collect": {"item": "коготь барса", "count": 7}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Горные хищники",
        "description": "Убейте 10 снежных барсов.",
        "quest_type": "side",
        "location": "mountains",
        "required_level": 15,
        "reward_exp": 110,
        "reward_coins": 100,
        "conditions": {"kill": {"animal": "Снежный барс", "count": 10}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    # Steppe quests - Степь
    {
        "title": "Суслики",
        "description": "Убейте 12 сусликов.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 18,
        "reward_exp": 260,
        "reward_coins": 200,
        "conditions": {"kill": {"animal": "Суслик", "count": 12}},
        "progress_reward": 10
    },
    {
        "title": "Дрофа",
        "description": "Убейте 8 дроф.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 19,
        "reward_exp": 300,
        "reward_coins": 240,
        "conditions": {"kill": {"animal": "Дрофа", "count": 8}},
        "progress_reward": 12
    },
    {
        "title": "Сайгак",
        "description": "Убейте 6 сайгаков.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 20,
        "reward_exp": 350,
        "reward_coins": 280,
        "conditions": {"kill": {"animal": "Сайгак", "count": 6}},
        "progress_reward": 13
    },
    {
        "title": "Антилопы",
        "description": "Убейте 10 антилоп.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 21,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Антилопа", "count": 10}},
        "progress_reward": 14
    },
    {
        "title": "Степные волки",
        "description": "Убейте 8 волков.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 22,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Волк", "count": 8}},
        "progress_reward": 15
    },
    {
        "title": "Гепард",
        "description": "Убейте 5 гепардов.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 23,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Гепард", "count": 5}},
        "progress_reward": 16
    },
    {
        "title": "Леопард",
        "description": "Убейте 4 леопарда.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 24,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Леопард", "count": 4}},
        "progress_reward": 17
    },
    {
        "title": "Гиены",
        "description": "Убейте 7 гиен.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 25,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Гиена", "count": 7}},
        "progress_reward": 18
    },
    {
        "title": "Лев",
        "description": "Убейте 3 льва.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 26,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Лев", "count": 3}},
        "progress_reward": 19
    },
    {
        "title": "Лев-людоед",
        "description": "Убейте легендарного льва-людоеда.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 27,
        "reward_exp": 900,
        "reward_coins": 720,
        "conditions": {"kill": {"animal": "Лев-людоед", "count": 1}},
        "progress_reward": 22
    },
    {
        "title": "Призрак степи",
        "description": "Убейте легендарного призрака степи.",
        "quest_type": "main",
        "location": "steppe",
        "required_level": 28,
        "reward_exp": 1200,
        "reward_coins": 950,
        "conditions": {"kill": {"animal": "Призрак степи", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Призрак степи"
    },
    # Side quests for steppe
    {
        "title": "Степные охотники",
        "description": "Убейте 15 антилоп.",
        "quest_type": "side",
        "location": "steppe",
        "required_level": 18,
        "reward_exp": 120,
        "reward_coins": 110,
        "conditions": {"kill": {"animal": "Антилопа", "count": 15}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Степные хищники",
        "description": "Убейте 12 львиц.",
        "quest_type": "side",
        "location": "steppe",
        "required_level": 20,
        "reward_exp": 130,
        "reward_coins": 120,
        "conditions": {"kill": {"animal": "Львица", "count": 12}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Гепардьи когти",
        "description": "Принесите 8 гепардьих когтей.",
        "quest_type": "side",
        "location": "steppe",
        "required_level": 23,
        "reward_exp": 140,
        "reward_coins": 130,
        "conditions": {"collect": {"item": "коготь гепарда", "count": 8}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Swamp quests - Болотo
    {
        "title": "Лягушки",
        "description": "Убейте 15 лягушек.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 22,
        "reward_exp": 280,
        "reward_coins": 220,
        "conditions": {"kill": {"animal": "Лягушка", "count": 15}},
        "progress_reward": 10
    },
    {
        "title": "Утки",
        "description": "Убейте 10 уток.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 23,
        "reward_exp": 320,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Утка", "count": 10}},
        "progress_reward": 12
    },
    {
        "title": "Черепахи",
        "description": "Убейте 8 черепах.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 24,
        "reward_exp": 360,
        "reward_coins": 290,
        "conditions": {"kill": {"animal": "Черепаха", "count": 8}},
        "progress_reward": 13
    },
    {
        "title": "Выдры",
        "description": "Убейте 6 выдр.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 25,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Выдра", "count": 6}},
        "progress_reward": 14
    },
    {
        "title": "Бобры",
        "description": "Убейте 5 бобров.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 26,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Бобр", "count": 5}},
        "progress_reward": 15
    },
    {
        "title": "Болотные кабаны",
        "description": "Убейте 7 болотных кабанов.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 27,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Болотный кабан", "count": 7}},
        "progress_reward": 16
    },
    {
        "title": "Питоны",
        "description": "Убейте 4 питонов.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 28,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Питон", "count": 4}},
        "progress_reward": 17
    },
    {
        "title": "Болотные волки",
        "description": "Убейте 5 болотных волков.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 29,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Болотный волк", "count": 5}},
        "progress_reward": 18
    },
    {
        "title": "Аллигаторы",
        "description": "Убейте 3 аллигатора.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 30,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Аллигатор", "count": 3}},
        "progress_reward": 19
    },
    {
        "title": "Гигантские крокодилы",
        "description": "Убейте 2 гигантских крокодила.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 31,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Гигантский крокодил", "count": 2}},
        "progress_reward": 20
    },
    {
        "title": "Дух болот",
        "description": "Убейте легендарного духа болот.",
        "quest_type": "main",
        "location": "swamp",
        "required_level": 32,
        "reward_exp": 1100,
        "reward_coins": 880,
        "conditions": {"kill": {"animal": "Дух болот", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Дух болот"
    },
    # Side quests for swamp
    {
        "title": "Болотные трофеи",
        "description": "Принесите 7 рысьих шкур.",
        "quest_type": "side",
        "location": "swamp",
        "required_level": 22,
        "reward_exp": 140,
        "reward_coins": 130,
        "conditions": {"collect": {"item": "шкура рыси", "count": 7}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Крокодильи зубы",
        "description": "Принесите 10 крокодильих зубов.",
        "quest_type": "side",
        "location": "swamp",
        "required_level": 30,
        "reward_exp": 160,
        "reward_coins": 150,
        "conditions": {"collect": {"item": "зуб крокодила", "count": 10}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Болотные хищники",
        "description": "Убейте 15 рысей.",
        "quest_type": "side",
        "location": "swamp",
        "required_level": 25,
        "reward_exp": 150,
        "reward_coins": 140,
        "conditions": {"kill": {"animal": "Рысь", "count": 15}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    # Deep forest quests - Глубокий лес
    {
        "title": "Тёмные белки",
        "description": "Убейте 10 белок.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 28,
        "reward_exp": 280,
        "reward_coins": 220,
        "conditions": {"kill": {"animal": "Белка", "count": 10}},
        "progress_reward": 10
    },
    {
        "title": "Лесные ежи",
        "description": "Убейте 12 ежей.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 29,
        "reward_exp": 320,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Еж", "count": 12}},
        "progress_reward": 12
    },
    {
        "title": "Ночные совы",
        "description": "Убейте 8 сов.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 30,
        "reward_exp": 360,
        "reward_coins": 290,
        "conditions": {"kill": {"animal": "Сова", "count": 8}},
        "progress_reward": 13
    },
    {
        "title": "Барсуки",
        "description": "Убейте 6 барсуков.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 31,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Барсук", "count": 6}},
        "progress_reward": 14
    },
    {
        "title": "Куницы",
        "description": "Убейте 8 куниц.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 32,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Куница", "count": 8}},
        "progress_reward": 15
    },
    {
        "title": "Тёмные кабаны",
        "description": "Убейте 7 кабанов.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 33,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Кабан", "count": 7}},
        "progress_reward": 16
    },
    {
        "title": "Лисы глубины",
        "description": "Убейте 6 лис.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 34,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Лиса", "count": 6}},
        "progress_reward": 17
    },
    {
        "title": "Рыси леса",
        "description": "Убейте 5 рысей.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 35,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Рысь", "count": 5}},
        "progress_reward": 18
    },
    {
        "title": "Волки стаи",
        "description": "Убейте 4 волка.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 36,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Волк", "count": 4}},
        "progress_reward": 19
    },
    {
        "title": "Олени леса",
        "description": "Убейте 3 оленя.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 37,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Олень", "count": 3}},
        "progress_reward": 20
    },
    {
        "title": "Лоси трофеи",
        "description": "Убейте 2 лося.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 38,
        "reward_exp": 750,
        "reward_coins": 600,
        "conditions": {"kill": {"animal": "Лось", "count": 2}},
        "progress_reward": 21
    },
    {
        "title": "Дух глухого леса",
        "description": "Убейте легендарного духа глухого леса.",
        "quest_type": "main",
        "location": "deep_forest",
        "required_level": 39,
        "reward_exp": 1100,
        "reward_coins": 880,
        "conditions": {"kill": {"animal": "Дух глухого леса", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Дух глухого леса"
    },
    # Side quests for deep_forest
    {
        "title": "Лесные великаны",
        "description": "Убейте 5 лосей.",
        "quest_type": "side",
        "location": "deep_forest",
        "required_level": 28,
        "reward_exp": 160,
        "reward_coins": 150,
        "conditions": {"kill": {"animal": "Лось", "count": 5}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Куньи шкуры",
        "description": "Принесите 9 куньих шкур.",
        "quest_type": "side",
        "location": "deep_forest",
        "required_level": 32,
        "reward_exp": 130,
        "reward_coins": 120,
        "conditions": {"collect": {"item": "шкура куницы", "count": 9}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Desert quests - Пустыня
    {
        "title": "Пустынный странник",
        "description": "Убейте 15 скорпионов.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 30,
        "reward_exp": 320,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Скорпион", "count": 15}},
        "progress_reward": 10
    },
    {
        "title": "Ящерицы",
        "description": "Убейте 20 ящериц.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 31,
        "reward_exp": 360,
        "reward_coins": 290,
        "conditions": {"kill": {"animal": "Ящерица", "count": 20}},
        "progress_reward": 12
    },
    {
        "title": "Вараны",
        "description": "Убейте 10 варанов.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 32,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Варан", "count": 10}},
        "progress_reward": 13
    },
    {
        "title": "Верблюды",
        "description": "Убейте 5 верблюдов.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 33,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Верблюд", "count": 5}},
        "progress_reward": 14
    },
    {
        "title": "Песчаные лисы",
        "description": "Убейте 8 песчаных лис.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 34,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Песчаная лиса", "count": 8}},
        "progress_reward": 15
    },
    {
        "title": "Пустынные волки",
        "description": "Убейте 6 пустынных волков.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 35,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Пустынный волк", "count": 6}},
        "progress_reward": 16
    },
    {
        "title": "Каракалы",
        "description": "Убейте 5 каракалов.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 36,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Каракал", "count": 5}},
        "progress_reward": 17
    },
    {
        "title": "Кобры",
        "description": "Убейте 4 кобры.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 37,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Кобра", "count": 4}},
        "progress_reward": 18
    },
    {
        "title": "Аддаксы",
        "description": "Убейте 3 аддакса.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 38,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Аддакс", "count": 3}},
        "progress_reward": 19
    },
    {
        "title": "Гигантские вараны",
        "description": "Убейте 2 гигантских варана.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 39,
        "reward_exp": 750,
        "reward_coins": 600,
        "conditions": {"kill": {"animal": "Гигантский варан", "count": 2}},
        "progress_reward": 20
    },
    {
        "title": "Дух пустыни",
        "description": "Убейте легендарного духа пустыни.",
        "quest_type": "main",
        "location": "desert",
        "required_level": 40,
        "reward_exp": 1100,
        "reward_coins": 880,
        "conditions": {"kill": {"animal": "Дух пустыни", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Дух пустыни"
    },
    # Side quests for desert
    {
        "title": "Пустынные сокровища",
        "description": "Принесите 12 скорпионьих жал.",
        "quest_type": "side",
        "location": "desert",
        "required_level": 30,
        "reward_exp": 180,
        "reward_coins": 170,
        "conditions": {"collect": {"item": "жало скорпиона", "count": 12}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Змеиная кожа",
        "description": "Принесите 8 змеиных шкур.",
        "quest_type": "side",
        "location": "desert",
        "required_level": 37,
        "reward_exp": 140,
        "reward_coins": 130,
        "conditions": {"collect": {"item": "шкура змеи", "count": 8}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Jungle quests - Джунгли
    {
        "title": "Попугаи",
        "description": "Убейте 15 попугаев.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 34,
        "reward_exp": 320,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Попугай", "count": 15}},
        "progress_reward": 10
    },
    {
        "title": "Обезьяны",
        "description": "Убейте 20 обезьян.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 35,
        "reward_exp": 360,
        "reward_coins": 290,
        "conditions": {"kill": {"animal": "Обезьяна", "count": 20}},
        "progress_reward": 12
    },
    {
        "title": "Туканы",
        "description": "Убейте 12 туканов.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 36,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Тукан", "count": 12}},
        "progress_reward": 13
    },
    {
        "title": "Капибары",
        "description": "Убейте 8 капибар.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 37,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Капибара", "count": 8}},
        "progress_reward": 14
    },
    {
        "title": "Анаконды",
        "description": "Убейте 6 анаконд.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 38,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Анаконда", "count": 6}},
        "progress_reward": 15
    },
    {
        "title": "Тапиры",
        "description": "Убейте 5 тапиров.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 39,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Тапир", "count": 5}},
        "progress_reward": 16
    },
    {
        "title": "Питоны",
        "description": "Убейте 4 питона.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 40,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Питон", "count": 4}},
        "progress_reward": 17
    },
    {
        "title": "Оцелоты",
        "description": "Убейте 5 оцелотов.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 41,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Оцелот", "count": 5}},
        "progress_reward": 18
    },
    {
        "title": "Ягуары",
        "description": "Убейте 4 ягуара.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 42,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Ягуар", "count": 4}},
        "progress_reward": 19
    },
    {
        "title": "Тигры",
        "description": "Убейте 3 тигра.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 43,
        "reward_exp": 750,
        "reward_coins": 600,
        "conditions": {"kill": {"animal": "Тигр", "count": 3}},
        "progress_reward": 20
    },
    {
        "title": "Дух амазонки",
        "description": "Убейте легендарного духа амазонки.",
        "quest_type": "main",
        "location": "jungle",
        "required_level": 44,
        "reward_exp": 1100,
        "reward_coins": 880,
        "conditions": {"kill": {"animal": "Дух амазонки", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Дух амазонки"
    },
    # Side quests for jungle
    {
        "title": "Джунгли полны опасностей",
        "description": "Убейте 25 обезьян.",
        "quest_type": "side",
        "location": "jungle",
        "required_level": 34,
        "reward_exp": 200,
        "reward_coins": 190,
        "conditions": {"kill": {"animal": "Обезьяна", "count": 25}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Ягуарьи когти",
        "description": "Принесите 7 ягуарьих когтей.",
        "quest_type": "side",
        "location": "jungle",
        "required_level": 42,
        "reward_exp": 150,
        "reward_coins": 140,
        "conditions": {"collect": {"item": "коготь ягуара", "count": 7}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Tundra quests - Тундра
    {
        "title": "Лемминги",
        "description": "Убейте 20 леммингов.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 38,
        "reward_exp": 320,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Лемминг", "count": 20}},
        "progress_reward": 10
    },
    {
        "title": "Полярные совы",
        "description": "Убейте 12 полярных сов.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 39,
        "reward_exp": 360,
        "reward_coins": 290,
        "conditions": {"kill": {"animal": "Полярная сова", "count": 12}},
        "progress_reward": 12
    },
    {
        "title": "Песцы",
        "description": "Убейте 10 песцов.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 40,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Песец", "count": 10}},
        "progress_reward": 13
    },
    {
        "title": "Северные олени",
        "description": "Убейте 6 северных оленей.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 41,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Северный олень", "count": 6}},
        "progress_reward": 14
    },
    {
        "title": "Полярные зайцы",
        "description": "Убейте 15 полярных зайцев.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 42,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Полярный заяц", "count": 15}},
        "progress_reward": 15
    },
    {
        "title": "Полярные волки",
        "description": "Убейте 8 полярных волков.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 43,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Полярный волк", "count": 8}},
        "progress_reward": 16
    },
    {
        "title": "Овцебыки",
        "description": "Убейте 4 овцебыка.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 44,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Овцебык", "count": 4}},
        "progress_reward": 17
    },
    {
        "title": "Моржи",
        "description": "Убейте 3 моржа.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 45,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Морж", "count": 3}},
        "progress_reward": 18
    },
    {
        "title": "Белые медведи",
        "description": "Убейте 2 белых медведя.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 46,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Белый медведь", "count": 2}},
        "progress_reward": 19
    },
    {
        "title": "Королевский морж",
        "description": "Убейте легендарного королевского моржа.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 47,
        "reward_exp": 900,
        "reward_coins": 720,
        "conditions": {"kill": {"animal": "Королевский морж", "count": 1}},
        "progress_reward": 22
    },
    {
        "title": "Дух арктики",
        "description": "Убейте легендарного духа арктики.",
        "quest_type": "main",
        "location": "tundra",
        "required_level": 48,
        "reward_exp": 1200,
        "reward_coins": 950,
        "conditions": {"kill": {"animal": "Дух арктики", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Дух арктики"
    },
    # Side quests for tundra
    {
        "title": "Ледяные трофеи",
        "description": "Принесите 10 медвежьих шкур.",
        "quest_type": "side",
        "location": "tundra",
        "required_level": 38,
        "reward_exp": 220,
        "reward_coins": 210,
        "conditions": {"collect": {"item": "шкура медведя", "count": 10}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Моржьи бивни",
        "description": "Принесите 6 моржьих бивней.",
        "quest_type": "side",
        "location": "tundra",
        "required_level": 45,
        "reward_exp": 170,
        "reward_coins": 160,
        "conditions": {"collect": {"item": "бивень моржа", "count": 6}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Savanna quests - Саванна
    {
        "title": "Сурикаты",
        "description": "Убейте 15 сурикатов.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 42,
        "reward_exp": 320,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Сурикат", "count": 15}},
        "progress_reward": 10
    },
    {
        "title": "Вараны",
        "description": "Убейте 12 варанов.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 43,
        "reward_exp": 360,
        "reward_coins": 290,
        "conditions": {"kill": {"animal": "Варан", "count": 12}},
        "progress_reward": 12
    },
    {
        "title": "Страусы",
        "description": "Убейте 8 страусов.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 44,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Страус", "count": 8}},
        "progress_reward": 13
    },
    {
        "title": "Газели",
        "description": "Убейте 10 газелей.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 45,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Газель", "count": 10}},
        "progress_reward": 14
    },
    {
        "title": "Зебры",
        "description": "Убейте 8 зебр.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 46,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Зебра", "count": 8}},
        "progress_reward": 15
    },
    {
        "title": "Гиеновые собаки",
        "description": "Убейте 7 гиеновых собак.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 47,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Гиеновая собака", "count": 7}},
        "progress_reward": 16
    },
    {
        "title": "Импалы",
        "description": "Убейте 6 импал.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 48,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Импала", "count": 6}},
        "progress_reward": 17
    },
    {
        "title": "Гепарды",
        "description": "Убейте 5 гепардов.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 49,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Гепард", "count": 5}},
        "progress_reward": 18
    },
    {
        "title": "Носороги",
        "description": "Убейте 3 носорога.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 50,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Носорог", "count": 3}},
        "progress_reward": 19
    },
    {
        "title": "Буйволы",
        "description": "Убейте 2 буйвола.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 51,
        "reward_exp": 750,
        "reward_coins": 600,
        "conditions": {"kill": {"animal": "Буйвол", "count": 2}},
        "progress_reward": 20
    },
    {
        "title": "Жирафы",
        "description": "Убейте 2 жирафа.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 52,
        "reward_exp": 800,
        "reward_coins": 640,
        "conditions": {"kill": {"animal": "Жираф", "count": 2}},
        "progress_reward": 21
    },
    {
        "title": "Слоны",
        "description": "Убейте слона.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 53,
        "reward_exp": 850,
        "reward_coins": 680,
        "conditions": {"kill": {"animal": "Слон", "count": 1}},
        "progress_reward": 22
    },
    {
        "title": "Дух саванны",
        "description": "Убейте легендарного духа саванны.",
        "quest_type": "main",
        "location": "savanna",
        "required_level": 54,
        "reward_exp": 1300,
        "reward_coins": 1050,
        "conditions": {"kill": {"animal": "Дух саванны", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Дух саванны"
    },
    # Side quests for savanna
    {
        "title": "Саванна полна жизни",
        "description": "Убейте 20 зебр.",
        "quest_type": "side",
        "location": "savanna",
        "required_level": 42,
        "reward_exp": 240,
        "reward_coins": 230,
        "conditions": {"kill": {"animal": "Зебра", "count": 20}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Слоновьи бивни",
        "description": "Принесите 4 слоновьих бивня.",
        "quest_type": "side",
        "location": "savanna",
        "required_level": 53,
        "reward_exp": 180,
        "reward_coins": 170,
        "conditions": {"collect": {"item": "бивень слона", "count": 4}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Ocean quests - Океан
    {
        "title": "Морской охотник",
        "description": "Убейте 20 акул.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 46,
        "reward_exp": 350,
        "reward_coins": 280,
        "conditions": {"kill": {"animal": "Акула", "count": 20}},
        "progress_reward": 10
    },
    {
        "title": "Киты",
        "description": "Убейте 10 китов.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 47,
        "reward_exp": 400,
        "reward_coins": 320,
        "conditions": {"kill": {"animal": "Кит", "count": 10}},
        "progress_reward": 12
    },
    {
        "title": "Морские черепахи",
        "description": "Убейте 15 морских черепах.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 48,
        "reward_exp": 450,
        "reward_coins": 360,
        "conditions": {"kill": {"animal": "Морская черепаха", "count": 15}},
        "progress_reward": 13
    },
    {
        "title": "Дельфины",
        "description": "Убейте 12 дельфинов.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 49,
        "reward_exp": 500,
        "reward_coins": 400,
        "conditions": {"kill": {"animal": "Дельфин", "count": 12}},
        "progress_reward": 14
    },
    {
        "title": "Морские котики",
        "description": "Убейте 8 морских котиков.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 50,
        "reward_exp": 550,
        "reward_coins": 440,
        "conditions": {"kill": {"animal": "Морской котик", "count": 8}},
        "progress_reward": 15
    },
    {
        "title": "Касатки",
        "description": "Убейте 6 касаток.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 51,
        "reward_exp": 600,
        "reward_coins": 480,
        "conditions": {"kill": {"animal": "Касатка", "count": 6}},
        "progress_reward": 16
    },
    {
        "title": "Гигантские акулы",
        "description": "Убейте 5 гигантских акул.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 52,
        "reward_exp": 650,
        "reward_coins": 520,
        "conditions": {"kill": {"animal": "Гигантская акула", "count": 5}},
        "progress_reward": 17
    },
    {
        "title": "Кашалоты",
        "description": "Убейте 4 кашалота.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 53,
        "reward_exp": 700,
        "reward_coins": 560,
        "conditions": {"kill": {"animal": "Кашалот", "count": 4}},
        "progress_reward": 18
    },
    {
        "title": "Мегалодон",
        "description": "Убейте легендарного мегалодона.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 54,
        "reward_exp": 900,
        "reward_coins": 720,
        "conditions": {"kill": {"animal": "Мегалодон", "count": 1}},
        "progress_reward": 22
    },
    {
        "title": "Кракен",
        "description": "Убейте легендарного кракена.",
        "quest_type": "main",
        "location": "ocean",
        "required_level": 55,
        "reward_exp": 1200,
        "reward_coins": 950,
        "conditions": {"kill": {"animal": "Кракен", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Кракен"
    },
    # Side quests for ocean
    {
        "title": "Морские трофеи",
        "description": "Принесите 15 акульих плавников.",
        "quest_type": "side",
        "location": "ocean",
        "required_level": 46,
        "reward_exp": 260,
        "reward_coins": 250,
        "conditions": {"collect": {"item": "плавник акулы", "count": 15}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Кашалотовы зубы",
        "description": "Принесите 8 кашалотовых зубов.",
        "quest_type": "side",
        "location": "ocean",
        "required_level": 53,
        "reward_exp": 190,
        "reward_coins": 180,
        "conditions": {"collect": {"item": "зуб кашалота", "count": 8}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Volcano quests - Вулкан
    {
        "title": "Огненное испытание",
        "description": "Убейте 35 огненных ящериц.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 50,
        "reward_exp": 380,
        "reward_coins": 310,
        "conditions": {"kill": {"animal": "Огненная ящерица", "count": 35}},
        "progress_reward": 10
    },
    {
        "title": "Пепельные ящерицы",
        "description": "Убейте 30 пепельных ящериц.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 51,
        "reward_exp": 420,
        "reward_coins": 340,
        "conditions": {"kill": {"animal": "Пепельная ящерица", "count": 30}},
        "progress_reward": 12
    },
    {
        "title": "Магматические вараны",
        "description": "Убейте 15 магматических варанов.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 52,
        "reward_exp": 470,
        "reward_coins": 380,
        "conditions": {"kill": {"animal": "Магматический варан", "count": 15}},
        "progress_reward": 13
    },
    {
        "title": "Огненные змеи",
        "description": "Убейте 10 огненных змей.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 53,
        "reward_exp": 520,
        "reward_coins": 420,
        "conditions": {"kill": {"animal": "Огненная змея", "count": 10}},
        "progress_reward": 14
    },
    {
        "title": "Пламенные скорпионы",
        "description": "Убейте 8 пламенных скорпионов.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 54,
        "reward_exp": 570,
        "reward_coins": 460,
        "conditions": {"kill": {"animal": "Пламенный скорпион", "count": 8}},
        "progress_reward": 15
    },
    {
        "title": "Огненные саламандры",
        "description": "Убейте 6 огненных саламандр.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 55,
        "reward_exp": 620,
        "reward_coins": 500,
        "conditions": {"kill": {"animal": "Огненная саламандра", "count": 6}},
        "progress_reward": 16
    },
    {
        "title": "Магматические драконы",
        "description": "Убейте 4 магматических дракона.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 56,
        "reward_exp": 670,
        "reward_coins": 540,
        "conditions": {"kill": {"animal": "Магматический дракон", "count": 4}},
        "progress_reward": 17
    },
    {
        "title": "Огненные фениксы",
        "description": "Убейте 3 огненных феникса.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 57,
        "reward_exp": 720,
        "reward_coins": 580,
        "conditions": {"kill": {"animal": "Огненный феникс", "count": 3}},
        "progress_reward": 18
    },
    {
        "title": "Огненный дракон",
        "description": "Убейте легендарного огненного дракона.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 58,
        "reward_exp": 950,
        "reward_coins": 760,
        "conditions": {"kill": {"animal": "Огненный дракон", "count": 1}},
        "progress_reward": 22
    },
    {
        "title": "Повелитель огня",
        "description": "Убейте легендарного повелителя огня.",
        "quest_type": "main",
        "location": "volcano",
        "required_level": 59,
        "reward_exp": 1300,
        "reward_coins": 1050,
        "conditions": {"kill": {"animal": "Повелитель огня", "count": 1}},
        "progress_reward": 25,
        "is_boss_quest": True,
        "boss_name": "Повелитель огня"
    },
    # Side quests for volcano
    {
        "title": "Огненные трофеи",
        "description": "Принесите 20 чешуек огненной ящерицы.",
        "quest_type": "side",
        "location": "volcano",
        "required_level": 50,
        "reward_exp": 280,
        "reward_coins": 270,
        "conditions": {"collect": {"item": "чешуйка ящерицы", "count": 20}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    {
        "title": "Драконьи чешуйки",
        "description": "Принесите 10 драконьих чешуек.",
        "quest_type": "side",
        "location": "volcano",
        "required_level": 58,
        "reward_exp": 200,
        "reward_coins": 190,
        "conditions": {"collect": {"item": "чешуйка дракона", "count": 10}},
        "progress_reward": 5,
        "is_repeatable": True
    },
    # Additional side quests for variety across all locations
    {
        "title": "Охота на кабанов",
        "description": "Убейте 15 кабанов.",
        "quest_type": "side",
        "location": "forest",
        "required_level": 5,
        "reward_exp": 70,
        "reward_coins": 60,
        "conditions": {"kill": {"animal": "Кабан", "count": 15}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Волчья стая",
        "description": "Убейте 20 волков.",
        "quest_type": "side",
        "location": "taiga",
        "required_level": 10,
        "reward_exp": 90,
        "reward_coins": 80,
        "conditions": {"kill": {"animal": "Волк", "count": 20}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Горные хищники",
        "description": "Убейте 10 снежных барсов.",
        "quest_type": "side",
        "location": "mountains",
        "required_level": 15,
        "reward_exp": 110,
        "reward_coins": 100,
        "conditions": {"kill": {"animal": "Снежный барс", "count": 10}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Степные хищники",
        "description": "Убейте 12 львиц.",
        "quest_type": "side",
        "location": "steppe",
        "required_level": 20,
        "reward_exp": 130,
        "reward_coins": 120,
        "conditions": {"kill": {"animal": "Львица", "count": 12}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Болотные хищники",
        "description": "Убейте 15 рысей.",
        "quest_type": "side",
        "location": "swamp",
        "required_level": 25,
        "reward_exp": 150,
        "reward_coins": 140,
        "conditions": {"kill": {"animal": "Рысь", "count": 15}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Лесные хищники",
        "description": "Убейте 18 волков.",
        "quest_type": "side",
        "location": "deep_forest",
        "required_level": 30,
        "reward_exp": 170,
        "reward_coins": 160,
        "conditions": {"kill": {"animal": "Волк", "count": 18}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Пустынные хищники",
        "description": "Убейте 14 каракалов.",
        "quest_type": "side",
        "location": "desert",
        "required_level": 35,
        "reward_exp": 190,
        "reward_coins": 180,
        "conditions": {"kill": {"animal": "Каракал", "count": 14}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Джунгли хищники",
        "description": "Убейте 16 оцелотов.",
        "quest_type": "side",
        "location": "jungle",
        "required_level": 40,
        "reward_exp": 210,
        "reward_coins": 200,
        "conditions": {"kill": {"animal": "Оцелот", "count": 16}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Арктические хищники",
        "description": "Убейте 12 полярных волков.",
        "quest_type": "side",
        "location": "tundra",
        "required_level": 45,
        "reward_exp": 230,
        "reward_coins": 220,
        "conditions": {"kill": {"animal": "Полярный волк", "count": 12}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Саванна хищники",
        "description": "Убейте 14 гепардов.",
        "quest_type": "side",
        "location": "savanna",
        "required_level": 50,
        "reward_exp": 250,
        "reward_coins": 240,
        "conditions": {"kill": {"animal": "Гепард", "count": 14}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Океан хищники",
        "description": "Убейте 18 акул.",
        "quest_type": "side",
        "location": "ocean",
        "required_level": 55,
        "reward_exp": 270,
        "reward_coins": 260,
        "conditions": {"kill": {"animal": "Акула", "count": 18}},
        "progress_reward": 4,
        "is_repeatable": True
    },
    {
        "title": "Вулкан хищники",
        "description": "Убейте 20 огненных ящериц.",
        "quest_type": "side",
        "location": "volcano",
        "required_level": 60,
        "reward_exp": 290,
        "reward_coins": 280,
        "conditions": {"kill": {"animal": "Огненная ящерица", "count": 20}},
        "progress_reward": 4,
        "is_repeatable": True
    }
]


async def seed_animals():
    """Seed animals from game_logic into database"""
    async with async_session() as session:
        for location, animals in ANIMALS_BY_LOCATION.items():
            for animal_data in animals:
                # Check if animal already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(Animal).where(Animal.name == animal_data.name)
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    animal = Animal(
                        name=animal_data.name,
                        emoji=animal_data.emoji,
                        location=location,
                        rarity=animal_data.rarity,
                        base_exp=animal_data.base_exp,
                        base_coins=animal_data.base_coins,
                        min_weight=animal_data.min_weight,
                        max_weight=animal_data.max_weight,
                        drop_chance=animal_data.drop_chance,
                        drops=animal_data.drops
                    )
                    session.add(animal)
        
        await session.commit()
        print("✅ Animals seeded successfully!")


async def seed_quests():
    """Seed quests into database"""
    async with async_session() as session:
        for quest_data in QUESTS_DATA:
            # Check if quest already exists
            from sqlalchemy import select
            result = await session.execute(
                select(Quest).where(Quest.title == quest_data["title"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                quest = Quest(**quest_data)
                session.add(quest)
        
        await session.commit()
        print("✅ Quests seeded successfully!")


async def main():
    await init_db()
    await seed_animals()
    await seed_quests()
    print("🎉 Database seeding completed!")


if __name__ == "__main__":
    asyncio.run(main())
