from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from bot.database.db import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    
    # Game mode
    game_mode = Column(String, default="free")  # "free" or "story"
    
    # Level and experience
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    
    # Energy
    energy = Column(Integer, default=100)
    max_energy = Column(Integer, default=100)
    last_energy_update = Column(DateTime, default=func.now())
    
    # Currency
    coins = Column(Integer, default=0)
    stars = Column(Integer, default=0)
    
    # Location
    current_location = Column(String, default="forest")
    location_progress = Column(JSON, default={})  # {"forest": 0, "taiga": 0, ...}
    
    # Hunt cooldown
    last_hunt_time = Column(DateTime, nullable=True)
    
    # Skills (JSON: {"accuracy": 0, "stealth": 0, "endurance": 0})
    skills = Column(JSON, default={"accuracy": 0, "stealth": 0, "endurance": 0})
    
    # Buffs
    active_buffs = Column(JSON, default={})  # {"track": {"expires": timestamp}, "ambush": {"expires": timestamp, "count": 3}}

    # Track uses counter (to prevent spamming "след" command)
    track_uses = Column(Integer, default=0)
    
    # Trap system
    trap_level = Column(Integer, default=0)  # 0=none, 1=trap, 2=pit, 3=auto_trap
    trap_active = Column(Boolean, default=False)
    trap_set_time = Column(DateTime, nullable=True)
    last_trap_time = Column(DateTime, nullable=True)  # For cooldown
    
    # Statistics - Free Mode
    total_hunts_free = Column(Integer, default=0)
    successful_hunts_free = Column(Integer, default=0)
    animals_killed_free = Column(JSON, default={})  # {"rabbit": 5, "deer": 2, ...}
    
    # Statistics - Story Mode
    total_hunts_story = Column(Integer, default=0)
    successful_hunts_story = Column(Integer, default=0)
    animals_killed_story = Column(JSON, default={})  # {"rabbit": 5, "deer": 2, ...}

    # Migrations / flags
    species_migrated = Column(Boolean, default=False)
    animal_species_migration_done = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    inventory_items = relationship("Inventory", back_populates="user", cascade="all, delete-orphan")
    weapons = relationship("Weapon", back_populates="user", cascade="all, delete-orphan")
    user_quests = relationship("UserQuest", back_populates="user", cascade="all, delete-orphan")
    trophies = relationship("Trophy", back_populates="user", cascade="all, delete-orphan")
    auction_lots = relationship("AuctionLot", back_populates="seller", cascade="all, delete-orphan")
    animal_species = relationship("AnimalSpecies", back_populates="user", cascade="all, delete-orphan")
    hunt_logs = relationship("HuntLog", cascade="all, delete-orphan")


class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    item_name = Column(String, nullable=False)
    item_type = Column(String, nullable=False)  # meat, skin, bone, horn, claw, bait, potion, etc.
    quantity = Column(Integer, default=1)
    rarity = Column(String, default="common")  # common, uncommon, rare, epic, legendary
    
    user = relationship("User", back_populates="inventory_items")


class Weapon(Base):
    __tablename__ = "weapons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    weapon_type = Column(String, nullable=False)  # bow, crossbow, rifle, shotgun
    level = Column(Integer, default=1)
    durability = Column(Integer, default=100)
    max_durability = Column(Integer, default=100)
    mods = Column(JSON, default={})  # {"scope": True, "silencer": False}
    
    is_equipped = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="weapons")


class Quest(Base):
    __tablename__ = "quests"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    quest_type = Column(String, nullable=False)  # main, side
    location = Column(String, nullable=False)
    required_level = Column(Integer, default=1)
    
    reward_exp = Column(Integer, default=0)
    reward_coins = Column(Integer, default=0)
    reward_items = Column(JSON, default=[])  # [{"item": "meat", "quantity": 5}]
    reward_stars = Column(Integer, default=0)
    
    conditions = Column(JSON, default={})  # {"kill": {"animal": "rabbit", "count": 5}, "collect": {"item": "skin", "count": 3}}
    progress_reward = Column(Integer, default=10)  # % progress to location
    
    is_repeatable = Column(Boolean, default=False)
    cooldown_hours = Column(Integer, default=24)
    
    # Boss quest
    is_boss_quest = Column(Boolean, default=False)
    boss_name = Column(String, nullable=True)


class UserQuest(Base):
    __tablename__ = "user_quests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False)
    
    status = Column(String, default="active")  # active, completed, failed
    progress = Column(JSON, default={})  # {"killed": 3, "collected": 1}
    
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="user_quests")
    quest = relationship("Quest")


class Animal(Base):
    __tablename__ = "animals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    emoji = Column(String, nullable=False)
    
    location = Column(String, nullable=False)
    rarity = Column(String, nullable=False)  # common, uncommon, rare, epic, legendary
    
    base_exp = Column(Integer, default=10)
    base_coins = Column(Integer, default=5)
    
    min_weight = Column(Float, default=1.0)
    max_weight = Column(Float, default=10.0)
    
    drop_chance = Column(Float, default=1.0)  # 0.0 to 1.0
    
    # Drops
    drops = Column(JSON, default={})  # {"meat": {"min": 1, "max": 3}, "skin": {"min": 1, "max": 1}}


class Trophy(Base):
    __tablename__ = "trophies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    animal_name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    
    is_displayed = Column(Boolean, default=False)
    
    date = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="trophies")


class AuctionLot(Base):
    __tablename__ = "auction_lots"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    item_name = Column(String, nullable=False)
    item_type = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    rarity = Column(String, default="common")

    price = Column(Integer, nullable=False)
    currency = Column(String, default="coins")  # coins, stars

    status = Column(String, default="active")  # active, sold, cancelled

    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)

    seller = relationship("User", back_populates="auction_lots")


class StarsTransaction(Base):
    __tablename__ = "stars_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    invoice_payload = Column(String, nullable=False)  # "guaranteed_hit", "skip_cooldown"
    invoice_link = Column(String, nullable=True)  # Generated invoice link
    amount = Column(Integer, nullable=False)  # Amount in stars

    status = Column(String, default="pending")  # pending, completed, failed, refunded

    telegram_payment_id = Column(String, nullable=True)  # Telegram payment ID
    error_message = Column(Text, nullable=True)

    # Store message_id and chat_id to reply to the original message after payment
    message_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")


class AnimalSpecies(Base):
    __tablename__ = "animal_species"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    animal_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    total_killed = Column(Integer, default=0)

    user = relationship("User", back_populates="animal_species")


class HuntLog(Base):
    __tablename__ = "hunt_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    animal_name = Column(String, nullable=False)
    animal_emoji = Column(String, nullable=False)
    location = Column(String, nullable=False)
    rarity = Column(String, nullable=False)

    weight = Column(Float, nullable=False)
    exp_gained = Column(Integer, default=0)
    coins_gained = Column(Integer, default=0)

    drops = Column(JSON, default={})  # {"Мясо": 2, "Шкура": 1}

    is_successful = Column(Boolean, default=True)
    game_mode = Column(String, default="free")  # free or story

    hunt_time = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="hunt_logs")
