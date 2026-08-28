from dataclasses import dataclass
from typing import Dict, List
import random


@dataclass
class AnimalData:
    name: str
    emoji: str
    rarity: str
    base_exp: int
    base_coins: int
    min_weight: float
    max_weight: float
    drop_chance: float
    drops: Dict[str, Dict[str, int]]
    sticker_file: str


# Rarity multipliers
RARITY_MULTIPLIERS = {
    "common": {"exp": 1.0, "coins": 1.0},
    "uncommon": {"exp": 1.5, "coins": 1.5},
    "rare": {"exp": 2.5, "coins": 2.5},
    "epic": {"exp": 4.0, "coins": 4.0},
    "legendary": {"exp": 7.0, "coins": 7.0}
}


# Animals by location
ANIMALS_BY_LOCATION = {
    "forest": [
        # Common animals
        AnimalData("Заяц", "🐰", "common", 10, 5, 2.0, 4.0, 0.12, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/forest/zayats.webp"),
        AnimalData("Белка", "🐿️", "common", 5, 3, 0.5, 1.0, 0.10, {"meat": {"min": 1, "max": 1}}, "stickers/forest/belka.webp"),
        AnimalData("Утка", "🦆", "common", 8, 4, 1.5, 3.0, 0.08, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 2, "max": 5}}, "stickers/forest/utka.webp"),
        AnimalData("Фазан", "🐔", "common", 12, 6, 1.0, 2.0, 0.07, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 6}}, "stickers/forest/fazan.webp"),
        AnimalData("Еж", "🦔", "common", 6, 4, 0.8, 1.5, 0.09, {"meat": {"min": 1, "max": 1}}, "stickers/forest/ezhed.webp"),
        AnimalData("Ворона", "🐦‍⬛", "common", 4, 2, 0.3, 0.6, 0.08, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 4}}, "stickers/forest/crow.webp"),
        AnimalData("Синица", "🐦", "common", 3, 2, 0.01, 0.02, 0.06, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 1, "max": 2}}, "stickers/forest/tit.webp"),
        AnimalData("Дятел", "🐦", "common", 5, 3, 0.05, 0.1, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 3}}, "stickers/forest/woodpecker.webp"),
        AnimalData("Горлица", "🐦", "common", 7, 4, 0.2, 0.4, 0.06, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 4}}, "stickers/forest/dove.webp"),
        # Uncommon animals
        AnimalData("Барсук", "🦡", "uncommon", 20, 12, 8.0, 15.0, 0.08, {"meat": {"min": 2, "max": 4}, "skin": {"min": 1, "max": 1}}, "stickers/forest/barsuk.webp"),
        AnimalData("Лиса", "🦊", "uncommon", 25, 15, 5.0, 8.0, 0.09, {"meat": {"min": 2, "max": 3}, "skin": {"min": 1, "max": 1}}, "stickers/forest/lisa.webp"),
        AnimalData("Рысь", "🐱", "uncommon", 30, 20, 15.0, 25.0, 0.06, {"meat": {"min": 3, "max": 5}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/forest/rys.webp"),
        AnimalData("Косуля", "🦌", "uncommon", 28, 18, 30.0, 45.0, 0.07, {"meat": {"min": 5, "max": 8}, "skin": {"min": 1, "max": 1}}, "stickers/forest/kosulya.webp"),
        AnimalData("Молодой кабан", "🐗", "uncommon", 30, 20, 40.0, 60.0, 0.06, {"meat": {"min": 6, "max": 10}, "skin": {"min": 1, "max": 1}}, "stickers/forest/kaban_molodoy.webp"),
        AnimalData("Енот", "🦝", "uncommon", 18, 10, 4.0, 8.0, 0.08, {"meat": {"min": 2, "max": 3}, "skin": {"min": 1, "max": 1}}, "stickers/forest/enot.webp"),
        AnimalData("Куница", "🦦", "uncommon", 22, 14, 1.5, 3.0, 0.05, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/forest/marten.webp"),
        AnimalData("Заяц-русак", "🐰", "uncommon", 14, 8, 3.0, 5.0, 0.06, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/forest/hare.webp"),
        AnimalData("Тетерев", "🦃", "uncommon", 15, 10, 0.8, 1.5, 0.05, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 4, "max": 8}}, "stickers/forest/grouse.webp"),
        AnimalData("Вальдшнеп", "🐦", "uncommon", 12, 7, 0.3, 0.5, 0.04, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 5}}, "stickers/forest/snip.webp"),
        # Rare animals
        AnimalData("Олень", "🦌", "rare", 60, 40, 80.0, 120.0, 0.06, {"meat": {"min": 10, "max": 15}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/forest/olen.webp"),
        AnimalData("Волк", "🐺", "rare", 55, 35, 30.0, 50.0, 0.05, {"meat": {"min": 5, "max": 8}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/forest/volk.webp"),
        AnimalData("Благородный олень", "🦌", "rare", 75, 52, 120.0, 180.0, 0.04, {"meat": {"min": 15, "max": 22}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/forest/deer.webp"),
        AnimalData("Лось", "🦌", "rare", 85, 58, 200.0, 350.0, 0.03, {"meat": {"min": 25, "max": 38}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/forest/moose.webp"),
        AnimalData("Зубр", "🦬", "rare", 95, 68, 400.0, 700.0, 0.02, {"meat": {"min": 45, "max": 65}, "skin": {"min": 1, "max": 1}, "horns": {"min": 2, "max": 2}}, "stickers/forest/bison.webp"),
        # Epic animals
        AnimalData("Кабан-секач", "🐗", "epic", 100, 70, 100.0, 150.0, 0.03, {"meat": {"min": 15, "max": 20}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 1, "max": 2}}, "stickers/forest/kaban_sekach.webp"),
        AnimalData("Медведь", "🐻", "epic", 120, 90, 150.0, 250.0, 0.02, {"meat": {"min": 20, "max": 30}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/forest/medved.webp"),
        AnimalData("Рыжий волк", "🐺", "epic", 110, 78, 35.0, 55.0, 0.015, {"meat": {"min": 6, "max": 10}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/forest/red_wolf.webp"),
        # Legendary animals
        AnimalData("Легендарный лось", "🦌", "legendary", 300, 200, 300.0, 400.0, 0.008, {"meat": {"min": 30, "max": 40}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/forest/legendary_los.webp"),
        AnimalData("Призрачный олень", "🦌", "legendary", 350, 240, 180.0, 280.0, 0.006, {"meat": {"min": 25, "max": 35}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/forest/ghost_deer.webp"),
    ],
    "taiga": [
        # Common animals
        AnimalData("Заяц-беляк", "🐰", "common", 12, 6, 2.5, 4.5, 0.12, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/taiga/zayats_belyak.webp"),
        AnimalData("Рябчик", "🐦", "common", 8, 5, 0.3, 0.5, 0.10, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 4}}, "stickers/taiga/ryabchik.webp"),
        AnimalData("Глухарь", "🦅", "common", 15, 8, 2.5, 4.0, 0.08, {"meat": {"min": 2, "max": 3}, "feathers": {"min": 5, "max": 8}}, "stickers/taiga/gluhar.webp"),
        AnimalData("Тетерев", "🦃", "common", 10, 6, 0.6, 1.2, 0.09, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 4, "max": 7}}, "stickers/taiga/grouse.webp"),
        AnimalData("Бурундук", "🐿️", "common", 7, 4, 0.08, 0.15, 0.08, {"meat": {"min": 1, "max": 1}}, "stickers/taiga/chipmunk.webp"),
        AnimalData("Поползень", "🐦", "common", 5, 3, 0.02, 0.04, 0.06, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 3}}, "stickers/taiga/nuthatch.webp"),
        AnimalData("Сойка", "🐦", "common", 6, 4, 0.15, 0.25, 0.07, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 5}}, "stickers/taiga/jay.webp"),
        # Uncommon animals
        AnimalData("Куница", "🦦", "uncommon", 22, 14, 1.5, 3.0, 0.08, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/taiga/kunitsa.webp"),
        AnimalData("Лисица", "🦊", "uncommon", 25, 15, 4.0, 7.0, 0.08, {"meat": {"min": 2, "max": 3}, "skin": {"min": 1, "max": 1}}, "stickers/taiga/lisitsa.webp"),
        AnimalData("Соболь", "🦦", "uncommon", 35, 25, 2.0, 4.0, 0.06, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/taiga/sobol.webp"),
        AnimalData("Росомаха", "🦡", "uncommon", 38, 28, 10.0, 18.0, 0.07, {"meat": {"min": 3, "max": 5}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 3}}, "stickers/taiga/rosomaha.webp"),
        AnimalData("Заяц-русак", "🐰", "uncommon", 14, 9, 3.0, 5.0, 0.06, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/taiga/hare.webp"),
        AnimalData("Белка-летяга", "🐿️", "uncommon", 18, 12, 0.15, 0.25, 0.05, {"meat": {"min": 1, "max": 1}, "skin": {"min": 1, "max": 1}}, "stickers/taiga/flying_squirrel.webp"),
        AnimalData("Ворон", "🐦‍⬛", "uncommon", 16, 10, 1.0, 1.5, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 4, "max": 6}}, "stickers/taiga/raven.webp"),
        # Rare animals
        AnimalData("Рысь", "🐱", "rare", 45, 30, 18.0, 30.0, 0.07, {"meat": {"min": 3, "max": 5}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/taiga/rys.webp"),
        AnimalData("Волк", "🐺", "rare", 55, 35, 35.0, 55.0, 0.08, {"meat": {"min": 5, "max": 8}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/taiga/volk.webp"),
        AnimalData("Кабан", "🐗", "rare", 65, 45, 90.0, 130.0, 0.06, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 1, "max": 2}}, "stickers/taiga/kaban.webp"),
        AnimalData("Северный олень", "🦌", "rare", 70, 48, 100.0, 170.0, 0.05, {"meat": {"min": 15, "max": 22}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/taiga/reindeer.webp"),
        AnimalData("Лось", "🦌", "rare", 80, 55, 250.0, 420.0, 0.04, {"meat": {"min": 28, "max": 42}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/taiga/moose.webp"),
        # Epic animals
        AnimalData("Медведь", "🐻", "epic", 130, 100, 200.0, 350.0, 0.03, {"meat": {"min": 25, "max": 35}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/taiga/medved.webp"),
        AnimalData("Амурский тигр", "🐯", "epic", 140, 110, 180.0, 250.0, 0.02, {"meat": {"min": 20, "max": 30}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/taiga/tigr.webp"),
        AnimalData("Бурый медведь", "🐻", "epic", 145, 108, 220.0, 380.0, 0.025, {"meat": {"min": 28, "max": 40}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 7}}, "stickers/taiga/brown_bear.webp"),
        # Legendary animals
        AnimalData("Снежный барс", "🐆", "legendary", 350, 250, 50.0, 80.0, 0.008, {"meat": {"min": 15, "max": 20}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/taiga/snezhny_bars.webp"),
        AnimalData("Дух тайги", "🐺", "legendary", 420, 300, 60.0, 90.0, 0.005, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 7}}, "stickers/taiga/spirit.webp"),
    ],
    "mountains": [
        # Common animals
        AnimalData("Горный козёл", "🐐", "common", 15, 8, 40.0, 70.0, 0.12, {"meat": {"min": 8, "max": 12}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/mountains/gorny_kozol.webp"),
        AnimalData("Сурок", "🦫", "common", 8, 5, 3.0, 6.0, 0.10, {"meat": {"min": 2, "max": 4}, "skin": {"min": 1, "max": 1}}, "stickers/mountains/surok.webp"),
        AnimalData("Горная куропатка", "🐦", "common", 10, 6, 0.4, 0.7, 0.09, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 3, "max": 5}}, "stickers/mountains/kuropatka.webp"),
        AnimalData("Альпийский вьюрок", "🐦", "common", 6, 4, 0.02, 0.04, 0.08, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 3}}, "stickers/mountains/finch.webp"),
        AnimalData("Горная пищуха", "🐭", "common", 5, 3, 0.04, 0.08, 0.07, {"meat": {"min": 1, "max": 1}}, "stickers/mountains/pika.webp"),
        AnimalData("Снежная полёвка", "🐭", "common", 4, 2, 0.02, 0.04, 0.06, {"meat": {"min": 1, "max": 1}}, "stickers/mountains/vole.webp"),
        # Uncommon animals
        AnimalData("Беркут", "🦅", "uncommon", 40, 25, 4.0, 7.0, 0.07, {"meat": {"min": 2, "max": 3}, "feathers": {"min": 5, "max": 10}}, "stickers/mountains/berkut.webp"),
        AnimalData("Горный баран", "🐑", "uncommon", 35, 22, 60.0, 100.0, 0.08, {"meat": {"min": 10, "max": 15}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/mountains/gorny_baran.webp"),
        AnimalData("Як", "🐃", "uncommon", 42, 28, 350.0, 500.0, 0.06, {"meat": {"min": 30, "max": 45}, "skin": {"min": 1, "max": 1}, "horns": {"min": 2, "max": 2}}, "stickers/mountains/yak.webp"),
        AnimalData("Гриф", "🦅", "uncommon", 28, 18, 3.0, 5.0, 0.05, {"meat": {"min": 2, "max": 3}, "feathers": {"min": 6, "max": 10}}, "stickers/mountains/vulture.webp"),
        AnimalData("Кеклик", "🐦", "uncommon", 14, 9, 0.5, 0.8, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 5}}, "stickers/mountains/chukar.webp"),
        # Rare animals
        AnimalData("Снежный барс", "🐆", "rare", 80, 55, 45.0, 75.0, 0.06, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/mountains/snezhny_bars.webp"),
        AnimalData("Пума", "🐆", "rare", 75, 50, 50.0, 85.0, 0.06, {"meat": {"min": 10, "max": 16}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/mountains/puma.webp"),
        AnimalData("Горный орёл", "🦅", "rare", 70, 48, 5.0, 8.0, 0.07, {"meat": {"min": 2, "max": 4}, "feathers": {"min": 8, "max": 12}, "claws": {"min": 2, "max": 3}}, "stickers/mountains/eagle.webp"),
        AnimalData("Альпийский горный козёл", "🐐", "rare", 55, 38, 70.0, 110.0, 0.05, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/mountains/ibex.webp"),
        AnimalData("Серна", "🦌", "rare", 48, 32, 35.0, 55.0, 0.05, {"meat": {"min": 8, "max": 12}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/mountains/chamois.webp"),
        # Epic animals
        AnimalData("Медведь гризли", "🐻", "epic", 135, 95, 200.0, 350.0, 0.035, {"meat": {"min": 25, "max": 38}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 8}}, "stickers/mountains/grizli.webp"),
        AnimalData("Горный лев", "🦁", "epic", 145, 105, 90.0, 140.0, 0.025, {"meat": {"min": 18, "max": 28}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/mountains/lion.webp"),
        AnimalData("Каменный козёл", "🐐", "epic", 95, 68, 80.0, 130.0, 0.02, {"meat": {"min": 14, "max": 22}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/mountains/stone_goat.webp"),
        # Legendary animals
        AnimalData("Легендарный як", "🐃", "legendary", 400, 300, 600.0, 900.0, 0.008, {"meat": {"min": 60, "max": 85}, "skin": {"min": 1, "max": 1}, "horns": {"min": 2, "max": 2}}, "stickers/mountains/legendary_yak.webp"),
        AnimalData("Властелин гор", "🦅", "legendary", 480, 360, 8.0, 12.0, 0.005, {"meat": {"min": 4, "max": 8}, "feathers": {"min": 15, "max": 25}, "claws": {"min": 6, "max": 9}}, "stickers/mountains/lord.webp"),
    ],
    "steppe": [
        # Common animals
        AnimalData("Суслик", "🐿️", "common", 5, 3, 0.5, 1.0, 0.12, {"meat": {"min": 1, "max": 1}}, "stickers/steppe/suslik.webp"),
        AnimalData("Дрофа", "🦅", "common", 10, 6, 3.0, 5.0, 0.08, {"meat": {"min": 2, "max": 3}, "feathers": {"min": 3, "max": 6}}, "stickers/steppe/drofa.webp"),
        AnimalData("Степной хорёк", "🦡", "common", 12, 7, 0.8, 1.5, 0.10, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/steppe/horek.webp"),
        AnimalData("Тушканчик", "🐭", "common", 4, 2, 0.08, 0.15, 0.09, {"meat": {"min": 1, "max": 1}}, "stickers/steppe/jerboa.webp"),
        AnimalData("Стрепет", "🐦", "common", 8, 5, 0.4, 0.7, 0.08, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 5}}, "stickers/steppe/bustard.webp"),
        AnimalData("Жаворонок", "🐦", "common", 4, 2, 0.03, 0.05, 0.07, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 3}}, "stickers/steppe/lark.webp"),
        AnimalData("Перепел", "🐦", "common", 5, 3, 0.1, 0.15, 0.06, {"meat": {"min": 1, "max": 1}}, "stickers/steppe/quail.webp"),
        # Uncommon animals
        AnimalData("Сайгак", "🦌", "uncommon", 32, 22, 35.0, 55.0, 0.09, {"meat": {"min": 8, "max": 13}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/steppe/saigak.webp"),
        AnimalData("Антилопа", "🦌", "uncommon", 30, 20, 50.0, 80.0, 0.10, {"meat": {"min": 8, "max": 12}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/steppe/antilopa.webp"),
        AnimalData("Шакал", "🐺", "uncommon", 25, 18, 12.0, 20.0, 0.08, {"meat": {"min": 4, "max": 6}, "skin": {"min": 1, "max": 1}}, "stickers/steppe/shakal.webp"),
        AnimalData("Степной орёл", "🦅", "uncommon", 38, 26, 4.5, 7.5, 0.07, {"meat": {"min": 2, "max": 4}, "feathers": {"min": 6, "max": 10}}, "stickers/steppe/orel.webp"),
        AnimalData("Волк", "🐺", "uncommon", 35, 24, 25.0, 40.0, 0.07, {"meat": {"min": 5, "max": 8}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 3}}, "stickers/steppe/wolf.webp"),
        AnimalData("Заяц-русак", "🐰", "uncommon", 14, 9, 3.0, 5.0, 0.06, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/steppe/hare.webp"),
        AnimalData("Дрофа-красотка", "🦅", "uncommon", 22, 15, 4.0, 7.0, 0.05, {"meat": {"min": 2, "max": 3}, "feathers": {"min": 5, "max": 8}}, "stickers/steppe/great_bustard.webp"),
        # Rare animals
        AnimalData("Гепард", "🐆", "rare", 70, 50, 45.0, 65.0, 0.06, {"meat": {"min": 10, "max": 15}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/steppe/gepard.webp"),
        AnimalData("Леопард", "🐆", "rare", 75, 52, 50.0, 75.0, 0.06, {"meat": {"min": 11, "max": 16}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/steppe/leopard.webp"),
        AnimalData("Гиена", "🐕", "rare", 60, 42, 40.0, 65.0, 0.07, {"meat": {"min": 8, "max": 12}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/steppe/giena.webp"),
        AnimalData("Корсак", "🐺", "rare", 32, 22, 8.0, 14.0, 0.05, {"meat": {"min": 3, "max": 5}, "skin": {"min": 1, "max": 1}}, "stickers/steppe/korsak.webp"),
        # Epic animals
        AnimalData("Лев", "🦁", "epic", 130, 95, 150.0, 250.0, 0.035, {"meat": {"min": 20, "max": 30}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/steppe/lev.webp"),
        AnimalData("Волк", "🐺", "epic", 85, 60, 45.0, 70.0, 0.025, {"meat": {"min": 8, "max": 12}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/steppe/wolf_alpha.webp"),
        # Legendary animals
        AnimalData("Лев-людоед", "🦁", "legendary", 380, 280, 200.0, 300.0, 0.008, {"meat": {"min": 25, "max": 35}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 8}}, "stickers/steppe/lev_lyudoyed.webp"),
        AnimalData("Призрак степи", "🦌", "legendary", 420, 310, 70.0, 100.0, 0.005, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/steppe/ghost.webp"),
    ],
    "desert": [
        # Common animals
        AnimalData("Тушканчик", "🐭", "common", 4, 2, 0.1, 0.2, 0.12, {"meat": {"min": 1, "max": 1}}, "stickers/desert/tushkanchik.webp"),
        AnimalData("Ящерица", "🦎", "common", 6, 3, 0.3, 0.6, 0.10, {"meat": {"min": 1, "max": 1}}, "stickers/desert/yasheritsa.webp"),
        AnimalData("Скорпион", "🦂", "common", 8, 5, 0.05, 0.1, 0.09, {"venom": {"min": 1, "max": 2}}, "stickers/desert/skorpion.webp"),
        AnimalData("Варан", "🦎", "common", 12, 7, 8.0, 15.0, 0.08, {"meat": {"min": 3, "max": 6}, "skin": {"min": 1, "max": 1}}, "stickers/desert/varan.webp"),
        AnimalData("Геккон", "🦎", "common", 5, 3, 0.02, 0.04, 0.07, {"meat": {"min": 1, "max": 1}}, "stickers/desert/gecko.webp"),
        AnimalData("Ушастый ёж", "🦔", "common", 7, 4, 0.4, 0.7, 0.06, {"meat": {"min": 1, "max": 1}}, "stickers/desert/hedgehog.webp"),
        AnimalData("Песчаная эфа", "🐍", "common", 15, 10, 0.3, 0.6, 0.05, {"venom": {"min": 2, "max": 4}, "skin": {"min": 1, "max": 1}}, "stickers/desert/viper.webp"),
        # Uncommon animals
        AnimalData("Верблюд", "🐫", "uncommon", 45, 30, 400.0, 600.0, 0.09, {"meat": {"min": 35, "max": 50}, "skin": {"min": 1, "max": 1}}, "stickers/desert/verblud.webp"),
        AnimalData("Песчаная лиса", "🦊", "uncommon", 28, 19, 3.0, 5.0, 0.08, {"meat": {"min": 2, "max": 3}, "skin": {"min": 1, "max": 1}}, "stickers/desert/fox.webp"),
        AnimalData("Пустынный волк", "🐺", "uncommon", 35, 24, 20.0, 35.0, 0.07, {"meat": {"min": 5, "max": 8}, "skin": {"min": 1, "max": 1}}, "stickers/desert/wolf.webp"),
        AnimalData("Стрела-змея", "🐍", "uncommon", 22, 15, 0.8, 1.5, 0.06, {"meat": {"min": 1, "max": 2}, "venom": {"min": 2, "max": 3}}, "stickers/desert/sand_snake.webp"),
        AnimalData("Агама", "🦎", "uncommon", 18, 12, 0.6, 1.2, 0.05, {"meat": {"min": 1, "max": 1}, "skin": {"min": 1, "max": 1}}, "stickers/desert/agama.webp"),
        # Rare animals
        AnimalData("Каракал", "🐱", "rare", 65, 45, 12.0, 18.0, 0.07, {"meat": {"min": 4, "max": 7}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/desert/karakal.webp"),
        AnimalData("Кобра", "🐍", "rare", 50, 35, 2.0, 4.0, 0.06, {"meat": {"min": 2, "max": 4}, "venom": {"min": 2, "max": 4}, "skin": {"min": 1, "max": 1}}, "stickers/desert/kobra.webp"),
        AnimalData("Фенек", "🦊", "rare", 38, 26, 1.5, 2.5, 0.05, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/desert/fennec.webp"),
        AnimalData("Аддакс", "🦌", "rare", 75, 52, 100.0, 150.0, 0.04, {"meat": {"min": 15, "max": 22}, "skin": {"min": 1, "max": 1}, "horns": {"min": 2, "max": 2}}, "stickers/desert/addax.webp"),
        # Epic animals
        AnimalData("Гигантский варан", "🦎", "epic", 95, 68, 50.0, 90.0, 0.035, {"meat": {"min": 15, "max": 25}, "skin": {"min": 1, "max": 1}}, "stickers/desert/giant_varan.webp"),
        AnimalData("Пустынный лев", "🦁", "epic", 140, 100, 140.0, 200.0, 0.025, {"meat": {"min": 20, "max": 30}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/desert/lion.webp"),
        # Legendary animals
        AnimalData("Королевская кобра", "🐍", "legendary", 380, 280, 8.0, 12.0, 0.008, {"meat": {"min": 5, "max": 10}, "venom": {"min": 10, "max": 15}, "skin": {"min": 1, "max": 1}}, "stickers/desert/king_cobra.webp"),
        AnimalData("Дух пустыни", "🐪", "legendary", 450, 340, 500.0, 750.0, 0.005, {"meat": {"min": 50, "max": 70}, "skin": {"min": 1, "max": 1}}, "stickers/desert/spirit.webp"),
    ],
    "jungle": [
        # Common animals
        AnimalData("Попугай", "🦜", "common", 6, 4, 0.4, 0.8, 0.10, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 6}}, "stickers/jungle/parrot.webp"),
        AnimalData("Обезьяна", "🐒", "common", 12, 7, 5.0, 12.0, 0.09, {"meat": {"min": 2, "max": 4}}, "stickers/jungle/monkey.webp"),
        AnimalData("Тукан", "🦜", "common", 10, 6, 0.6, 1.2, 0.08, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 4, "max": 7}}, "stickers/jungle/tukan.webp"),
        AnimalData("Игуана", "🦎", "common", 8, 5, 3.0, 6.0, 0.08, {"meat": {"min": 2, "max": 4}}, "stickers/jungle/iguana.webp"),
        AnimalData("Лягушка", "🐸", "common", 4, 2, 0.05, 0.15, 0.07, {"meat": {"min": 1, "max": 1}}, "stickers/jungle/frog.webp"),
        AnimalData("Бабочка", "🦋", "common", 2, 1, 0.001, 0.003, 0.05, {"feathers": {"min": 1, "max": 2}}, "stickers/jungle/butterfly.webp"),
        AnimalData("Скорпион", "🦂", "common", 7, 4, 0.02, 0.05, 0.06, {"venom": {"min": 1, "max": 2}}, "stickers/jungle/scorpion.webp"),
        AnimalData("Паук", "🕷️", "common", 5, 3, 0.01, 0.03, 0.05, {"venom": {"min": 1, "max": 2}}, "stickers/jungle/spider.webp"),
        # Uncommon animals
        AnimalData("Капибара", "🦫", "uncommon", 25, 16, 35.0, 65.0, 0.09, {"meat": {"min": 8, "max": 13}, "skin": {"min": 1, "max": 1}}, "stickers/jungle/kapibara.webp"),
        AnimalData("Анаконда", "🐍", "uncommon", 38, 26, 30.0, 80.0, 0.07, {"meat": {"min": 10, "max": 18}, "skin": {"min": 1, "max": 1}}, "stickers/jungle/anakonda.webp"),
        AnimalData("Тапир", "🦛", "uncommon", 32, 22, 150.0, 250.0, 0.08, {"meat": {"min": 15, "max": 25}, "skin": {"min": 1, "max": 1}}, "stickers/jungle/tapir.webp"),
        AnimalData("Питон", "🐍", "uncommon", 42, 29, 40.0, 100.0, 0.06, {"meat": {"min": 12, "max": 20}, "skin": {"min": 1, "max": 1}}, "stickers/jungle/python.webp"),
        AnimalData("Мартышка", "🐒", "uncommon", 15, 10, 3.0, 6.0, 0.06, {"meat": {"min": 1, "max": 2}}, "stickers/jungle/marmoset.webp"),
        AnimalData("Шипохвост", "🦎", "uncommon", 20, 13, 8.0, 15.0, 0.05, {"meat": {"min": 3, "max": 5}, "skin": {"min": 1, "max": 1}}, "stickers/jungle/uromastyx.webp"),
        # Rare animals
        AnimalData("Оцелот", "🐆", "rare", 58, 40, 11.0, 16.0, 0.06, {"meat": {"min": 4, "max": 6}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/jungle/otselot.webp"),
        AnimalData("Ягуар", "🐆", "rare", 85, 60, 56.0, 96.0, 0.05, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/jungle/yaguar.webp"),
        AnimalData("Древесный удав", "🐍", "rare", 48, 33, 15.0, 35.0, 0.04, {"meat": {"min": 6, "max": 12}, "skin": {"min": 1, "max": 1}}, "stickers/jungle/tree_boa.webp"),
        AnimalData("Броненосец", "🐢", "rare", 35, 24, 5.0, 12.0, 0.04, {"meat": {"min": 4, "max": 8}, "shell": {"min": 1, "max": 1}}, "stickers/jungle/armadillo.webp"),
        # Epic animals
        AnimalData("Тигр", "🐯", "epic", 145, 105, 90.0, 180.0, 0.03, {"meat": {"min": 18, "max": 28}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 7}}, "stickers/jungle/tiger.webp"),
        AnimalData("Горилла", "🦍", "epic", 125, 90, 140.0, 220.0, 0.025, {"meat": {"min": 20, "max": 30}}, "stickers/jungle/gorilla.webp"),
        AnimalData("Леопард", "🐆", "epic", 115, 82, 55.0, 85.0, 0.02, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/jungle/leopard.webp"),
        # Legendary animals
        AnimalData("Король джунглей", "🦁", "legendary", 450, 340, 250.0, 380.0, 0.008, {"meat": {"min": 30, "max": 45}, "skin": {"min": 1, "max": 1}, "claws": {"min": 6, "max": 10}}, "stickers/jungle/king.webp"),
        AnimalData("Дух амазонки", "🐆", "legendary", 520, 390, 70.0, 110.0, 0.005, {"meat": {"min": 15, "max": 25}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 8}}, "stickers/jungle/spirit.webp"),
    ],
    "swamp": [
        # Common animals
        AnimalData("Лягушка", "🐸", "common", 3, 2, 0.1, 0.3, 0.12, {"meat": {"min": 1, "max": 1}}, "stickers/swamp/lyagushka.webp"),
        AnimalData("Утка", "🦆", "common", 8, 4, 1.5, 3.0, 0.09, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 2, "max": 5}}, "stickers/swamp/utka.webp"),
        AnimalData("Черепаха", "🐢", "common", 7, 5, 5.0, 15.0, 0.08, {"meat": {"min": 3, "max": 6}, "shell": {"min": 1, "max": 1}}, "stickers/swamp/cherepaha.webp"),
        AnimalData("Цапля", "🦩", "common", 12, 7, 1.5, 3.0, 0.07, {"meat": {"min": 2, "max": 3}, "feathers": {"min": 4, "max": 6}}, "stickers/swamp/heron.webp"),
        AnimalData("Тритон", "🦎", "common", 5, 3, 0.02, 0.05, 0.07, {"meat": {"min": 1, "max": 1}}, "stickers/swamp/newt.webp"),
        AnimalData("Болотный паук", "🕷️", "common", 4, 2, 0.01, 0.02, 0.05, {"venom": {"min": 1, "max": 2}}, "stickers/swamp/spider.webp"),
        AnimalData("Водяной уж", "🐍", "common", 10, 6, 0.5, 1.5, 0.06, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/swamp/water_snake.webp"),
        # Uncommon animals
        AnimalData("Выдра", "🦦", "uncommon", 28, 18, 5.0, 10.0, 0.07, {"meat": {"min": 3, "max": 5}, "skin": {"min": 1, "max": 1}}, "stickers/swamp/vydra.webp"),
        AnimalData("Бобр", "🦫", "uncommon", 26, 17, 15.0, 30.0, 0.08, {"meat": {"min": 4, "max": 7}, "skin": {"min": 1, "max": 1}}, "stickers/swamp/bobr.webp"),
        AnimalData("Ондатра", "🐀", "uncommon", 15, 10, 0.8, 1.5, 0.06, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/swamp/muskrat.webp"),
        AnimalData("Пеликан", "🦅", "uncommon", 22, 14, 5.0, 10.0, 0.05, {"meat": {"min": 3, "max": 5}, "feathers": {"min": 6, "max": 10}}, "stickers/swamp/pelican.webp"),
        # Rare animals
        AnimalData("Болотный кабан", "🐗", "rare", 62, 42, 90.0, 140.0, 0.07, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 1, "max": 2}}, "stickers/swamp/kaban.webp"),
        AnimalData("Питон", "🐍", "rare", 70, 48, 50.0, 120.0, 0.06, {"meat": {"min": 15, "max": 25}, "skin": {"min": 1, "max": 1}}, "stickers/swamp/piton.webp"),
        AnimalData("Гигантская выдра", "🦦", "rare", 45, 32, 8.0, 15.0, 0.05, {"meat": {"min": 4, "max": 8}, "skin": {"min": 1, "max": 1}}, "stickers/swamp/giant_otter.webp"),
        AnimalData("Болотный волк", "🐺", "rare", 58, 40, 30.0, 50.0, 0.05, {"meat": {"min": 6, "max": 10}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/swamp/wolf.webp"),
        # Epic animals
        AnimalData("Аллигатор", "🐊", "epic", 120, 85, 150.0, 300.0, 0.03, {"meat": {"min": 20, "max": 30}, "skin": {"min": 1, "max": 1}, "teeth": {"min": 5, "max": 10}}, "stickers/swamp/alligator.webp"),
        AnimalData("Гигантский крокодил", "🐊", "epic", 135, 98, 200.0, 400.0, 0.025, {"meat": {"min": 25, "max": 38}, "skin": {"min": 1, "max": 1}, "teeth": {"min": 8, "max": 12}}, "stickers/swamp/giant_croc.webp"),
        # Legendary animals
        AnimalData("Болотный кайман", "🐊", "legendary", 380, 280, 300.0, 500.0, 0.008, {"meat": {"min": 35, "max": 50}, "skin": {"min": 1, "max": 1}, "teeth": {"min": 12, "max": 18}}, "stickers/swamp/kaiman.webp"),
        AnimalData("Дух болот", "🐊", "legendary", 450, 340, 350.0, 550.0, 0.005, {"meat": {"min": 40, "max": 60}, "skin": {"min": 1, "max": 1}, "teeth": {"min": 10, "max": 15}}, "stickers/swamp/spirit.webp"),
    ],
    "tundra": [
        # Common animals
        AnimalData("Лемминг", "🐭", "common", 5, 3, 0.05, 0.1, 0.12, {"meat": {"min": 1, "max": 1}}, "stickers/tundra/lemming.webp"),
        AnimalData("Полярная сова", "🦉", "common", 14, 8, 1.5, 2.5, 0.09, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 5, "max": 8}}, "stickers/tundra/owl.webp"),
        AnimalData("Белая куропатка", "🐦", "common", 9, 6, 0.4, 0.6, 0.10, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 5}}, "stickers/tundra/ptarmigan.webp"),
        AnimalData("Песец", "🦊", "common", 22, 14, 2.5, 6.0, 0.08, {"meat": {"min": 2, "max": 4}, "skin": {"min": 1, "max": 1}}, "stickers/tundra/fox.webp"),
        AnimalData("Заяц-беляк", "🐰", "common", 10, 6, 2.0, 4.0, 0.08, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/tundra/hare.webp"),
        AnimalData("Тундряная куропатка", "🐦", "common", 8, 5, 0.3, 0.5, 0.07, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 4}}, "stickers/tundra/rock_ptarmigan.webp"),
        AnimalData("Поморник", "🐦", "common", 6, 4, 0.5, 0.8, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 5}}, "stickers/tundra/skua.webp"),
        # Uncommon animals
        AnimalData("Северный олень", "🦌", "uncommon", 40, 28, 90.0, 150.0, 0.08, {"meat": {"min": 15, "max": 22}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/tundra/olen.webp"),
        AnimalData("Полярный заяц", "🐰", "uncommon", 24, 16, 3.5, 6.0, 0.08, {"meat": {"min": 2, "max": 3}, "skin": {"min": 1, "max": 1}}, "stickers/tundra/hare_arctic.webp"),
        AnimalData("Горностай", "🦦", "uncommon", 18, 12, 0.1, 0.2, 0.06, {"meat": {"min": 1, "max": 1}, "skin": {"min": 1, "max": 1}}, "stickers/tundra/stoat.webp"),
        AnimalData("Ласка", "🦦", "uncommon", 14, 9, 0.08, 0.15, 0.05, {"meat": {"min": 1, "max": 1}, "skin": {"min": 1, "max": 1}}, "stickers/tundra/weasel.webp"),
        # Rare animals
        AnimalData("Полярный волк", "🐺", "rare", 68, 48, 40.0, 70.0, 0.07, {"meat": {"min": 8, "max": 13}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/tundra/wolf.webp"),
        AnimalData("Овцебык", "🦬", "rare", 75, 52, 200.0, 350.0, 0.06, {"meat": {"min": 25, "max": 38}, "skin": {"min": 1, "max": 1}, "horns": {"min": 2, "max": 2}}, "stickers/tundra/musk_ox.webp"),
        AnimalData("Северный олень", "🦌", "rare", 55, 38, 120.0, 200.0, 0.05, {"meat": {"min": 18, "max": 28}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/tundra/reindeer.webp"),
        # Epic animals
        AnimalData("Морж", "🦭", "epic", 115, 82, 800.0, 1500.0, 0.035, {"meat": {"min": 40, "max": 60}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 2, "max": 2}}, "stickers/tundra/walrus.webp"),
        AnimalData("Белый медведь", "🐻‍❄️", "epic", 155, 115, 250.0, 450.0, 0.025, {"meat": {"min": 30, "max": 45}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 8}}, "stickers/tundra/polar_bear.webp"),
        # Legendary animals
        AnimalData("Королевский морж", "🦭", "legendary", 450, 330, 1500.0, 2500.0, 0.008, {"meat": {"min": 70, "max": 100}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 2, "max": 2}}, "stickers/tundra/king_walrus.webp"),
        AnimalData("Дух арктики", "🐻‍❄️", "legendary", 520, 390, 350.0, 500.0, 0.005, {"meat": {"min": 45, "max": 65}, "skin": {"min": 1, "max": 1}, "claws": {"min": 6, "max": 9}}, "stickers/tundra/spirit.webp"),
    ],
    "savanna": [
        # Common animals
        AnimalData("Сурикат", "🦡", "common", 6, 4, 0.7, 1.0, 0.10, {"meat": {"min": 1, "max": 1}}, "stickers/savanna/surrikat.webp"),
        AnimalData("Варан", "🦎", "common", 11, 6, 10.0, 20.0, 0.08, {"meat": {"min": 4, "max": 8}, "skin": {"min": 1, "max": 1}}, "stickers/savanna/varan.webp"),
        AnimalData("Страус", "🦤", "common", 16, 9, 60.0, 130.0, 0.07, {"meat": {"min": 15, "max": 25}, "feathers": {"min": 8, "max": 15}}, "stickers/savanna/straus.webp"),
        AnimalData("Цапля", "🦩", "common", 10, 6, 1.5, 3.0, 0.06, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 4, "max": 7}}, "stickers/savanna/heron.webp"),
        AnimalData("Ткачик", "🐦", "common", 4, 2, 0.02, 0.04, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 3}}, "stickers/savanna/weaver.webp"),
        AnimalData("Мартышка-верветка", "🐒", "common", 8, 5, 3.0, 6.0, 0.06, {"meat": {"min": 1, "max": 2}}, "stickers/savanna/vervet.webp"),
        AnimalData("Африканский ёж", "🦔", "common", 6, 4, 0.6, 1.2, 0.05, {"meat": {"min": 1, "max": 1}}, "stickers/savanna/hedgehog.webp"),
        # Uncommon animals
        AnimalData("Газель", "🦌", "uncommon", 35, 24, 30.0, 60.0, 0.09, {"meat": {"min": 8, "max": 14}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/savanna/gazel.webp"),
        AnimalData("Зебра", "🦓", "uncommon", 42, 29, 200.0, 380.0, 0.08, {"meat": {"min": 20, "max": 32}, "skin": {"min": 1, "max": 1}}, "stickers/savanna/zebra.webp"),
        AnimalData("Гиеновая собака", "🐕", "uncommon", 38, 26, 20.0, 35.0, 0.07, {"meat": {"min": 5, "max": 9}, "skin": {"min": 1, "max": 1}}, "stickers/savanna/wild_dog.webp"),
        AnimalData("Импала", "🦌", "uncommon", 28, 19, 35.0, 60.0, 0.07, {"meat": {"min": 8, "max": 12}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/savanna/impala.webp"),
        AnimalData("Койот", "🐺", "uncommon", 32, 22, 15.0, 25.0, 0.06, {"meat": {"min": 4, "max": 7}, "skin": {"min": 1, "max": 1}}, "stickers/savanna/coyote.webp"),
        # Rare animals
        AnimalData("Гепард", "🐆", "rare", 78, 55, 50.0, 70.0, 0.06, {"meat": {"min": 11, "max": 17}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/savanna/cheetah.webp"),
        AnimalData("Носорог", "🦏", "rare", 95, 68, 1200.0, 2300.0, 0.05, {"meat": {"min": 60, "max": 90}, "skin": {"min": 1, "max": 1}, "horn": {"min": 1, "max": 1}}, "stickers/savanna/rhino.webp"),
        AnimalData("Буйвол", "🐃", "rare", 88, 62, 400.0, 750.0, 0.04, {"meat": {"min": 50, "max": 75}, "skin": {"min": 1, "max": 1}, "horns": {"min": 2, "max": 2}}, "stickers/savanna/buffalo.webp"),
        AnimalData("Сервал", "🐆", "rare", 52, 36, 12.0, 20.0, 0.04, {"meat": {"min": 4, "max": 7}, "skin": {"min": 1, "max": 1}}, "stickers/savanna/serval.webp"),
        # Epic animals
        AnimalData("Жираф", "🦒", "epic", 110, 80, 800.0, 1900.0, 0.035, {"meat": {"min": 50, "max": 75}, "skin": {"min": 1, "max": 1}}, "stickers/savanna/giraffe.webp"),
        AnimalData("Слон", "🐘", "epic", 160, 120, 3000.0, 6000.0, 0.025, {"meat": {"min": 80, "max": 120}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 2, "max": 2}}, "stickers/savanna/elephant.webp"),
        AnimalData("Лев", "🦁", "epic", 135, 98, 160.0, 260.0, 0.03, {"meat": {"min": 22, "max": 32}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/savanna/lion.webp"),
        # Legendary animals
        AnimalData("Король саванны", "🦁", "legendary", 500, 380, 220.0, 320.0, 0.008, {"meat": {"min": 32, "max": 48}, "skin": {"min": 1, "max": 1}, "claws": {"min": 6, "max": 10}}, "stickers/savanna/king_lion.webp"),
        AnimalData("Дух саванны", "🐘", "legendary", 580, 440, 4500.0, 7000.0, 0.005, {"meat": {"min": 100, "max": 150}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 2, "max": 2}}, "stickers/savanna/spirit.webp"),
    ],
    "rainforest": [
        # Common animals
        AnimalData("Лягушка-древолаз", "🐸", "common", 4, 3, 0.02, 0.05, 0.10, {"venom": {"min": 1, "max": 2}}, "stickers/rainforest/poison_frog.webp"),
        AnimalData("Колибри", "🐦", "common", 7, 4, 0.01, 0.02, 0.09, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 4}}, "stickers/rainforest/hummingbird.webp"),
        AnimalData("Ленивец", "🦥", "common", 10, 6, 3.0, 6.0, 0.08, {"meat": {"min": 2, "max": 4}}, "stickers/rainforest/sloth.webp"),
        AnimalData("Древесная лягушка", "🐸", "common", 5, 3, 0.05, 0.1, 0.08, {"meat": {"min": 1, "max": 1}}, "stickers/rainforest/tree_frog.webp"),
        AnimalData("Бабочка", "🦋", "common", 3, 2, 0.002, 0.005, 0.07, {"feathers": {"min": 1, "max": 2}}, "stickers/rainforest/butterfly.webp"),
        AnimalData("Попугай-ара", "🦜", "common", 12, 7, 0.8, 1.2, 0.06, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 4, "max": 7}}, "stickers/rainforest/macaw.webp"),
        AnimalData("Опоссум", "🦝", "common", 8, 5, 2.0, 4.0, 0.06, {"meat": {"min": 2, "max": 3}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/opossum.webp"),
        # Uncommon animals
        AnimalData("Тамарин", "🐒", "uncommon", 22, 14, 0.3, 0.6, 0.09, {"meat": {"min": 1, "max": 1}}, "stickers/rainforest/tamarin.webp"),
        AnimalData("Коати", "🦝", "uncommon", 28, 18, 3.0, 6.0, 0.08, {"meat": {"min": 2, "max": 4}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/coati.webp"),
        AnimalData("Древесный кенгуру", "🦘", "uncommon", 35, 24, 8.0, 15.0, 0.07, {"meat": {"min": 4, "max": 8}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/tree_kangaroo.webp"),
        AnimalData("Игуана", "🦎", "uncommon", 20, 13, 5.0, 12.0, 0.06, {"meat": {"min": 3, "max": 6}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/iguana.webp"),
        AnimalData("Питон", "🐍", "uncommon", 45, 32, 40.0, 90.0, 0.05, {"meat": {"min": 12, "max": 20}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/python.webp"),
        # Rare animals
        AnimalData("Пантера", "🐆", "rare", 82, 58, 50.0, 100.0, 0.06, {"meat": {"min": 12, "max": 20}, "skin": {"min": 1, "max": 1}, "claws": {"min": 3, "max": 5}}, "stickers/rainforest/panther.webp"),
        AnimalData("Анаконда", "🐍", "rare", 88, 62, 70.0, 150.0, 0.05, {"meat": {"min": 18, "max": 30}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/anaconda.webp"),
        AnimalData("Тапир", "🦛", "rare", 55, 38, 180.0, 300.0, 0.04, {"meat": {"min": 20, "max": 32}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/tapir.webp"),
        AnimalData("Оцелот", "🐆", "rare", 48, 33, 10.0, 18.0, 0.04, {"meat": {"min": 4, "max": 7}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/ocelot.webp"),
        # Epic animals
        AnimalData("Казуар", "🦤", "epic", 105, 75, 40.0, 85.0, 0.035, {"meat": {"min": 12, "max": 20}, "feathers": {"min": 10, "max": 18}, "claws": {"min": 2, "max": 3}}, "stickers/rainforest/cassowary.webp"),
        AnimalData("Гарпия", "🦅", "epic", 130, 95, 6.0, 9.0, 0.025, {"meat": {"min": 3, "max": 6}, "feathers": {"min": 12, "max": 20}, "claws": {"min": 4, "max": 6}}, "stickers/rainforest/harpy_eagle.webp"),
        # Legendary animals
        AnimalData("Легендарная анаконда", "🐍", "legendary", 480, 360, 200.0, 300.0, 0.008, {"meat": {"min": 50, "max": 75}, "skin": {"min": 1, "max": 1}}, "stickers/rainforest/legendary_anaconda.webp"),
        AnimalData("Дух дождевого леса", "🐆", "legendary", 550, 420, 80.0, 130.0, 0.005, {"meat": {"min": 18, "max": 28}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 8}}, "stickers/rainforest/spirit.webp"),
    ],
    "north_forest": [
        # Common animals
        AnimalData("Белка", "🐿️", "common", 6, 4, 0.4, 0.9, 0.10, {"meat": {"min": 1, "max": 1}}, "stickers/north_forest/belka.webp"),
        AnimalData("Дятел", "🐦", "common", 8, 5, 0.08, 0.15, 0.08, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 4}}, "stickers/north_forest/woodpecker.webp"),
        AnimalData("Заяц", "🐰", "common", 10, 6, 2.0, 4.0, 0.09, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/north_forest/hare.webp"),
        AnimalData("Сойка", "🐦", "common", 7, 4, 0.15, 0.25, 0.07, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 3, "max": 5}}, "stickers/north_forest/jay.webp"),
        AnimalData("Поползень", "🐦", "common", 6, 4, 0.02, 0.04, 0.06, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 3}}, "stickers/north_forest/nuthatch.webp"),
        AnimalData("Ворона", "🐦‍⬛", "common", 5, 3, 0.3, 0.6, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 4}}, "stickers/north_forest/crow.webp"),
        # Uncommon animals
        AnimalData("Бобр", "🦫", "uncommon", 30, 20, 18.0, 35.0, 0.09, {"meat": {"min": 5, "max": 10}, "skin": {"min": 1, "max": 1}}, "stickers/north_forest/beaver.webp"),
        AnimalData("Рысь", "🐱", "uncommon", 38, 26, 18.0, 30.0, 0.08, {"meat": {"min": 4, "max": 7}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/north_forest/lynx.webp"),
        AnimalData("Росомаха", "🦡", "uncommon", 42, 28, 12.0, 20.0, 0.07, {"meat": {"min": 3, "max": 6}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 3}}, "stickers/north_forest/wolverine.webp"),
        AnimalData("Заяц-беляк", "🐰", "uncommon", 14, 9, 2.5, 4.5, 0.06, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/north_forest/snowshoe_hare.webp"),
        AnimalData("Глухарь", "🦅", "uncommon", 18, 12, 2.5, 4.5, 0.05, {"meat": {"min": 2, "max": 3}, "feathers": {"min": 5, "max": 8}}, "stickers/north_forest/capercaillie.webp"),
        # Rare animals
        AnimalData("Лось", "🦌", "rare", 72, 50, 350.0, 550.0, 0.07, {"meat": {"min": 35, "max": 55}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/north_forest/moose.webp"),
        AnimalData("Волк", "🐺", "rare", 65, 45, 35.0, 55.0, 0.06, {"meat": {"min": 7, "max": 12}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/north_forest/wolf.webp"),
        AnimalData("Северный олень", "🦌", "rare", 68, 47, 150.0, 280.0, 0.05, {"meat": {"min": 22, "max": 35}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/north_forest/reindeer.webp"),
        AnimalData("Бурый медведь", "🐻", "rare", 95, 68, 180.0, 320.0, 0.04, {"meat": {"min": 25, "max": 38}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/north_forest/brown_bear.webp"),
        # Epic animals
        AnimalData("Гризли", "🐻", "epic", 145, 105, 220.0, 380.0, 0.035, {"meat": {"min": 28, "max": 42}, "skin": {"min": 1, "max": 1}, "claws": {"min": 5, "max": 8}}, "stickers/north_forest/grizzly.webp"),
        AnimalData("Лесной бизон", "🦬", "epic", 125, 90, 500.0, 900.0, 0.025, {"meat": {"min": 50, "max": 75}, "skin": {"min": 1, "max": 1}, "horns": {"min": 2, "max": 2}}, "stickers/north_forest/bison.webp"),
        # Legendary animals
        AnimalData("Легендарный медведь", "🐻", "legendary", 520, 400, 400.0, 600.0, 0.008, {"meat": {"min": 50, "max": 70}, "skin": {"min": 1, "max": 1}, "claws": {"min": 8, "max": 12}}, "stickers/north_forest/legendary_bear.webp"),
        AnimalData("Дух северного леса", "🦌", "legendary", 580, 440, 500.0, 750.0, 0.005, {"meat": {"min": 55, "max": 80}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/north_forest/spirit.webp"),
    ],
    "deep_forest": [
        # Common animals
        AnimalData("Белка", "🐿️", "common", 5, 3, 0.5, 1.0, 0.10, {"meat": {"min": 1, "max": 1}}, "stickers/deep_forest/belka.webp"),
        AnimalData("Еж", "🦔", "common", 6, 4, 0.8, 1.5, 0.08, {"meat": {"min": 1, "max": 1}}, "stickers/deep_forest/ezhed.webp"),
        AnimalData("Сова", "🦉", "common", 10, 6, 1.0, 2.0, 0.07, {"meat": {"min": 1, "max": 2}, "feathers": {"min": 4, "max": 7}}, "stickers/deep_forest/owl.webp"),
        AnimalData("Дятел", "🐦", "common", 7, 4, 0.06, 0.12, 0.06, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 4}}, "stickers/deep_forest/woodpecker.webp"),
        AnimalData("Воробей", "🐦", "common", 3, 2, 0.02, 0.03, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 1, "max": 2}}, "stickers/deep_forest/sparrow.webp"),
        AnimalData("Поползень", "🐦", "common", 5, 3, 0.02, 0.04, 0.05, {"meat": {"min": 1, "max": 1}, "feathers": {"min": 2, "max": 3}}, "stickers/deep_forest/nuthatch.webp"),
        # Uncommon animals
        AnimalData("Барсук", "🦡", "uncommon", 28, 18, 10.0, 18.0, 0.08, {"meat": {"min": 3, "max": 6}, "skin": {"min": 1, "max": 1}}, "stickers/deep_forest/badger.webp"),
        AnimalData("Куница", "🦦", "uncommon", 32, 22, 1.5, 3.0, 0.07, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/deep_forest/kunitsa.webp"),
        AnimalData("Кабан", "🐗", "uncommon", 44, 30, 85.0, 130.0, 0.06, {"meat": {"min": 12, "max": 18}, "skin": {"min": 1, "max": 1}, "tusks": {"min": 1, "max": 2}}, "stickers/deep_forest/boar.webp"),
        AnimalData("Лиса", "🦊", "uncommon", 30, 20, 5.0, 9.0, 0.06, {"meat": {"min": 3, "max": 5}, "skin": {"min": 1, "max": 1}}, "stickers/deep_forest/fox.webp"),
        AnimalData("Заяц-русак", "🐰", "uncommon", 15, 10, 3.0, 5.0, 0.05, {"meat": {"min": 1, "max": 2}, "skin": {"min": 1, "max": 1}}, "stickers/deep_forest/hare.webp"),
        # Rare animals
        AnimalData("Рысь", "🐱", "rare", 50, 35, 20.0, 35.0, 0.07, {"meat": {"min": 4, "max": 6}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/deep_forest/rys.webp"),
        AnimalData("Волк", "🐺", "rare", 60, 40, 40.0, 60.0, 0.07, {"meat": {"min": 6, "max": 10}, "skin": {"min": 1, "max": 1}, "claws": {"min": 2, "max": 4}}, "stickers/deep_forest/volk.webp"),
        AnimalData("Олень", "🦌", "rare", 68, 46, 100.0, 180.0, 0.05, {"meat": {"min": 15, "max": 25}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/deep_forest/deer.webp"),
        AnimalData("Лось", "🦌", "rare", 82, 58, 280.0, 450.0, 0.04, {"meat": {"min": 32, "max": 50}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/deep_forest/moose.webp"),
        # Epic animals
        AnimalData("Медведь", "🐻", "epic", 125, 90, 180.0, 300.0, 0.035, {"meat": {"min": 25, "max": 35}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/deep_forest/medved.webp"),
        AnimalData("Вожак стаи", "🐺", "epic", 135, 100, 55.0, 80.0, 0.025, {"meat": {"min": 10, "max": 15}, "skin": {"min": 1, "max": 1}, "claws": {"min": 4, "max": 6}}, "stickers/deep_forest/alpha_wolf.webp"),
        # Legendary animals
        AnimalData("Великий лось", "🦌", "legendary", 450, 320, 500.0, 700.0, 0.008, {"meat": {"min": 40, "max": 50}, "skin": {"min": 1, "max": 1}, "horns": {"min": 1, "max": 1}}, "stickers/deep_forest/veliky_los.webp"),
        AnimalData("Дух глухого леса", "🐻", "legendary", 520, 390, 300.0, 450.0, 0.005, {"meat": {"min": 40, "max": 60}, "skin": {"min": 1, "max": 1}, "claws": {"min": 6, "max": 9}}, "stickers/deep_forest/spirit.webp"),
    ],
}


def get_animals_for_location(location: str) -> List[AnimalData]:
    return ANIMALS_BY_LOCATION.get(location, ANIMALS_BY_LOCATION["forest"])


def select_random_animal(location: str, track_buff: bool = False, bait_type: str = None) -> AnimalData:
    animals = get_animals_for_location(location)
    
    # Filter by bait type if specified
    if bait_type:
        if bait_type == "herbivore":
            animals = [a for a in animals if a.name in ["Заяц", "Белка", "Олень", "Косуля", "Лось", "Антилопа", "Горный козёл", "Горный баран"]]
        elif bait_type == "predator":
            animals = [a for a in animals if a.name in ["Лиса", "Волк", "Рысь", "Медведь", "Лев", "Гепард", "Барс"]]
    
    # Apply track buff (increases rare animal chance)
    if track_buff:
        # Increase weights for rare+ animals
        weights = []
        for animal in animals:
            if animal.rarity in ["rare", "epic", "legendary"]:
                weights.append(animal.drop_chance * 2)
            else:
                weights.append(animal.drop_chance * 0.5)
    else:
        weights = [a.drop_chance for a in animals]
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        return random.choice(animals)
    
    normalized_weights = [w / total_weight for w in weights]
    
    return random.choices(animals, weights=normalized_weights, k=1)[0]


def calculate_rewards(animal: AnimalData, weight: float) -> tuple[int, int]:
    """Calculate exp and coins based on animal rarity and weight"""
    multipliers = RARITY_MULTIPLIERS.get(animal.rarity, RARITY_MULTIPLIERS["common"])
    
    # Weight bonus (heavier = more rewards)
    weight_bonus = 1 + (weight - animal.min_weight) / (animal.max_weight - animal.min_weight + 1) * 0.5
    
    exp = int(animal.base_exp * multipliers["exp"] * weight_bonus)
    coins = int(animal.base_coins * multipliers["coins"] * weight_bonus)
    
    return exp, coins


def generate_drops(animal: AnimalData) -> Dict[str, int]:
    """Generate random drops based on animal's drop table"""
    drops = {}
    
    for item_name, range_data in animal.drops.items():
        quantity = random.randint(range_data["min"], range_data["max"])
        if quantity > 0:
            drops[item_name] = quantity
    
    return drops



# Animal strength levels (for wound mechanics) - INCREASED KILL CHANCES
ANIMAL_STRENGTH = {
    "common": {"bow_kill_chance": 0.98, "crossbow_kill_chance": 1.0, "rifle_kill_chance": 1.0, "shotgun_kill_chance": 1.0},
    "uncommon": {"bow_kill_chance": 0.90, "crossbow_kill_chance": 0.98, "rifle_kill_chance": 1.0, "shotgun_kill_chance": 1.0},
    "rare": {"bow_kill_chance": 0.70, "crossbow_kill_chance": 0.90, "rifle_kill_chance": 1.0, "shotgun_kill_chance": 0.98},
    "epic": {"bow_kill_chance": 0.35, "crossbow_kill_chance": 0.65, "rifle_kill_chance": 0.95, "shotgun_kill_chance": 0.85},
    "legendary": {"bow_kill_chance": 0.10, "crossbow_kill_chance": 0.30, "rifle_kill_chance": 0.80, "shotgun_kill_chance": 0.60},
}


def can_kill_animal(weapon_type: str, animal: AnimalData) -> tuple[bool, float]:
    """
    Determine if weapon can kill the animal or just wound it.
    
    Returns:
        tuple: (killed, kill_chance)
            - killed: True if animal is killed, False if wounded
            - kill_chance: Probability of kill for displaying
    """
    strength = ANIMAL_STRENGTH.get(animal.rarity, ANIMAL_STRENGTH["common"])
    kill_chance = strength.get(f"{weapon_type}_kill_chance", 1.0)
    
    # Roll for kill
    roll = random.random()
    killed = roll <= kill_chance
    
    return killed, kill_chance
