from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from bot.database.models import User, Inventory, Weapon, Quest, UserQuest, Animal, Trophy, AuctionLot, StarsTransaction
from datetime import datetime, timedelta
from bot.config import MAX_ENERGY, ENERGY_REGEN_PASSIVE


ALL_LOCATION_KEYS = [
    "forest", "taiga", "mountains", "steppe",
    "desert", "jungle", "swamp", "tundra",
    "savanna", "rainforest", "north_forest", "deep_forest",
    "ocean", "volcano"
]


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str = None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        default_progress = {k: 0 for k in ALL_LOCATION_KEYS}
        user = User(
            telegram_id=telegram_id,
            username=username,
            game_mode="free",
            location_progress=default_progress
        )
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
        except Exception:
            # Handle race condition: another request created the user first
            await session.rollback()
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if not user:
                # If still not found, re-raise the original exception
                raise
    else:
        # Update username if it changed
        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        
        # Ensure location_progress has all keys (for users created before new locations were added)
        if not user.location_progress:
            user.location_progress = {}
        progress = user.location_progress
        added = False
        for k in ALL_LOCATION_KEYS:
            if k not in progress:
                progress[k] = 0
                added = True
        if added:
            flag_modified(user, "location_progress")
            changed = True

        # Ensure statistics JSON dicts are initialized
        if user.animals_killed_free is None:
            user.animals_killed_free = {}
            flag_modified(user, "animals_killed_free")
            changed = True
        if user.animals_killed_story is None:
            user.animals_killed_story = {}
            flag_modified(user, "animals_killed_story")
            changed = True
        if user.active_buffs is None:
            user.active_buffs = {}
            flag_modified(user, "active_buffs")
            changed = True
        if user.skills is None:
            user.skills = {"accuracy": 0, "stealth": 0, "endurance": 0}
            flag_modified(user, "skills")
            changed = True

        if changed:
            await session.commit()
            await session.refresh(user)
    
    return user


async def update_energy(session: AsyncSession, user: User) -> User:
    """Passive energy recovery: +1 every 5 minutes"""
    now = datetime.utcnow()
    if user.last_energy_update:
        time_diff = (now - user.last_energy_update).total_seconds()
        minutes_passed = int(time_diff / 60) // 5
        energy_gain = minutes_passed * ENERGY_REGEN_PASSIVE
        
        if energy_gain > 0:
            user.energy = min(user.max_energy, user.energy + energy_gain)
            user.last_energy_update = now
            await session.commit()
            await session.refresh(user)
    
    return user


async def consume_energy(session: AsyncSession, user: User, amount: int) -> bool:
    user = await update_energy(session, user)
    
    if user.energy >= amount:
        user.energy -= amount
        await session.commit()
        await session.refresh(user)
        return True
    return False


async def add_energy(session: AsyncSession, user: User, amount: int) -> User:
    user.energy = min(user.max_energy, user.energy + amount)
    user.last_energy_update = datetime.utcnow()
    await session.commit()
    await session.refresh(user)
    return user


async def create_stars_transaction(
    session: AsyncSession,
    user_id: int,
    invoice_payload: str,
    invoice_link: str,
    amount: int,
    message_id: int = None,
    chat_id: int = None
) -> StarsTransaction:
    transaction = StarsTransaction(
        user_id=user_id,
        invoice_payload=invoice_payload,
        invoice_link=invoice_link,
        amount=amount,
        status="pending",
        message_id=message_id,
        chat_id=chat_id
    )
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


async def update_stars_transaction(
    session: AsyncSession,
    transaction_id: int,
    status: str,
    telegram_payment_id: str = None,
    error_message: str = None
) -> StarsTransaction:
    result = await session.execute(select(StarsTransaction).where(StarsTransaction.id == transaction_id))
    transaction = result.scalar_one_or_none()

    if transaction:
        transaction.status = status
        if telegram_payment_id:
            transaction.telegram_payment_id = telegram_payment_id
        if error_message:
            transaction.error_message = error_message
        await session.commit()
        await session.refresh(transaction)

    return transaction


async def can_hunt(user: User) -> tuple[bool, str, int, int]:
    """Check if user can hunt (energy and cooldown)"""
    if user.energy < 5:
        return False, "Недостаточно энергии! (нужно 5)", 0, 0

    if user.last_hunt_time:
        cooldown_remaining = (user.last_hunt_time + timedelta(seconds=600)) - datetime.utcnow()
        if cooldown_remaining.total_seconds() > 0:
            total_seconds = int(cooldown_remaining.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return False, f"Кулдаун: {minutes} мин. Пропустить за 1 ⭐", minutes, seconds

    return True, "", 0, 0


async def update_hunt_cooldown(session: AsyncSession, user: User) -> User:
    user.last_hunt_time = datetime.utcnow()
    await session.commit()
    await session.refresh(user)
    return user


async def add_inventory_item(session: AsyncSession, user_id: int, item_name: str, item_type: str, quantity: int = 1, rarity: str = "common") -> Inventory:
    result = await session.execute(
        select(Inventory).where(
            and_(
                Inventory.user_id == user_id,
                Inventory.item_name == item_name,
                Inventory.item_type == item_type,
                Inventory.rarity == rarity
            )
        )
    )
    item = result.scalar_one_or_none()
    
    if item:
        item.quantity += quantity
    else:
        item = Inventory(
            user_id=user_id,
            item_name=item_name,
            item_type=item_type,
            quantity=quantity,
            rarity=rarity
        )
        session.add(item)
    
    await session.commit()
    await session.refresh(item)
    return item


async def consume_inventory_item(session: AsyncSession, user_id: int, item_name: str, item_type: str, quantity: int = 1) -> bool:
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[CONSUME] Looking for: user_id={user_id}, name='{item_name}', type='{item_type}', quantity={quantity}")

    # Log all items for this user to debug
    all_items_result = await session.execute(
        select(Inventory).where(Inventory.user_id == user_id)
    )
    all_items = all_items_result.scalars().all()
    for item in all_items:
        logger.info(f"[CONSUME] User has item: name='{item.item_name}', type='{item.item_type}', quantity={item.quantity}")

    result = await session.execute(
        select(Inventory).where(
            and_(
                Inventory.user_id == user_id,
                Inventory.item_name == item_name,
                Inventory.item_type == item_type
            )
        )
    )
    item = result.scalar_one_or_none()

    logger.info(f"[CONSUME] Found item: {item is not None}")

    if item and item.quantity >= quantity:
        item.quantity -= quantity
        if item.quantity <= 0:
            await session.delete(item)
        await session.commit()
        logger.info(f"[CONSUME] Successfully consumed {quantity} of {item_name}")
        return True
    logger.warning(f"[CONSUME] Failed to consume: item={item is not None}, quantity={item.quantity if item else 0}, needed={quantity}")
    return False


async def update_location_progress(session: AsyncSession, user: User, location: str, progress_add: float) -> User:
    if not user.location_progress:
        user.location_progress = {}
    
    current = user.location_progress.get(location, 0)
    new_progress = min(100, current + progress_add)
    user.location_progress[location] = new_progress
    flag_modified(user, "location_progress")
    
    await session.commit()
    await session.refresh(user)
    return user


async def add_exp(session: AsyncSession, user: User, exp: int) -> User:
    user.exp += exp
    
    # Level up logic: exponential curve - harder to level up
    exp_needed = user.level * user.level * 100
    while user.exp >= exp_needed:
        user.exp -= exp_needed
        user.level += 1
        exp_needed = user.level * user.level * 100
    
    await session.commit()
    await session.refresh(user)
    return user


async def add_coins(session: AsyncSession, user: User, coins: int) -> User:
    user.coins += coins
    await session.commit()
    await session.refresh(user)
    return user


async def get_animals_by_location(session: AsyncSession, location: str) -> list[Animal]:
    result = await session.execute(select(Animal).where(Animal.location == location))
    return result.scalars().all()


async def get_equipped_weapon(session: AsyncSession, user_id: int) -> Weapon:
    result = await session.execute(
        select(Weapon).where(and_(Weapon.user_id == user_id, Weapon.is_equipped == True))
    )
    return result.scalar_one_or_none()


async def add_species_kill(session: AsyncSession, user_id: int, animal_name: str, location: str, add_count: int = 1):
    from bot.database.models import AnimalSpecies
    result = await session.execute(
        select(AnimalSpecies).where(
            and_(
                AnimalSpecies.user_id == user_id,
                AnimalSpecies.animal_name == animal_name,
                AnimalSpecies.location == location,
            )
        )
    )
    sp = result.scalar_one_or_none()
    if sp:
        sp.total_killed += add_count
    else:
        sp = AnimalSpecies(
            user_id=user_id,
            animal_name=animal_name,
            location=location,
            total_killed=add_count,
        )
        session.add(sp)
    await session.commit()


async def get_species_for_user(session: AsyncSession, user_id: int) -> dict:
    from bot.database.models import AnimalSpecies
    result = await session.execute(
        select(AnimalSpecies).where(AnimalSpecies.user_id == user_id)
    )
    species = result.scalars().all()
    by_loc: dict[str, list[tuple[str, int]]] = {}
    total_kinds = 0
    total_killed = 0
    for s in species:
        by_loc.setdefault(s.location, []).append((s.animal_name, s.total_killed))
        total_kinds += 1
        total_killed += s.total_killed
    return {"by_location": by_loc, "kinds": total_kinds, "killed": total_killed}


async def get_active_quests(session: AsyncSession, user_id: int) -> list[UserQuest]:
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(UserQuest).options(selectinload(UserQuest.quest)).where(
            UserQuest.user_id == user_id, UserQuest.status == "active"
        )
    )
    return result.scalars().all()


async def get_available_quests(session: AsyncSession, user_level: int, user_id: int,
                                location_ids: list[str] | None = None, allow_repeatable=True) -> list[Quest]:
    user_quests_result = await session.execute(
        select(UserQuest.quest_id, UserQuest.status).where(UserQuest.user_id == user_id)
    )
    user_rows = user_quests_result.all()
    active_quest_ids = {r[0] for r in user_rows if r[1] == "active"}
    completed_non_repeatable = set()
    completed_repeatable_last_done = {}
    from bot.database.models import UserQuest as _UQ
    res = await session.execute(
        select(_UQ).where(_UQ.user_id == user_id, _UQ.status == "completed")
    )
    for uq in res.scalars().all():
        if uq.quest_id in active_quest_ids:
            continue
        q_stmt = await session.execute(select(Quest).where(Quest.id == uq.quest_id))
        q = q_stmt.scalar_one_or_none()
        if not q:
            continue
        if q.is_repeatable and allow_repeatable:
            prev = completed_repeatable_last_done.get(q.id)
            if prev is None or (uq.completed_at and uq.completed_at > prev):
                completed_repeatable_last_done[q.id] = uq.completed_at or datetime.min
        else:
            completed_non_repeatable.add(q.id)

    taken_blocked = completed_non_repeatable | active_quest_ids

    clauses = [Quest.required_level <= user_level]
    if location_ids:
        clauses.append(Quest.location.in_(location_ids))

    result = await session.execute(select(Quest).where(and_(*clauses)).order_by(Quest.location, Quest.quest_type, Quest.required_level))
    quests = result.scalars().all()
    return [q for q in quests if q.id not in taken_blocked]


async def get_top_players_by_level(session: AsyncSession, limit: int = 10) -> list[User]:
    result = await session.execute(
        select(User).order_by(User.level.desc(), User.exp.desc()).limit(limit)
    )
    return result.scalars().all()


async def log_hunt(session: AsyncSession, user_id: int, animal_name: str, animal_emoji: str,
                location: str, rarity: str, weight: float, exp: int, coins: int,
                drops: dict, is_successful: bool, game_mode: str):
    """Log a hunt to the HuntLog table. Note: caller must commit the session."""
    from bot.database.models import HuntLog
    from bot.game_logic.animals import drop_to_ru

    # Convert drops to Russian names
    drops_ru = {}
    for item, quantity in drops.items():
        ru_name = drop_to_ru(item)
        drops_ru[ru_name] = drops_ru.get(ru_name, 0) + quantity

    hunt_log = HuntLog(
        user_id=user_id,
        animal_name=animal_name,
        animal_emoji=animal_emoji,
        location=location,
        rarity=rarity,
        weight=weight,
        exp_gained=exp,
        coins_gained=coins,
        drops=drops_ru,
        is_successful=is_successful,
        game_mode=game_mode
    )
    session.add(hunt_log)


async def migrate_animal_species(session: AsyncSession) -> bool:
    """Migrate existing animal kill data to AnimalSpecies table. Returns True if migration was performed."""
    from bot.database.models import AnimalSpecies
    from bot.game_logic.animals import get_animal_location
    import logging

    logger = logging.getLogger(__name__)

    # Check if migration already done (check if any user has the flag set)
    result = await session.execute(select(User).where(User.animal_species_migration_done == True).limit(1))
    already_migrated = result.scalar_one_or_none()

    if already_migrated:
        logger.info("AnimalSpecies migration already done, skipping.")
        return False

    logger.info("Starting AnimalSpecies migration...")

    # Get all users
    result = await session.execute(select(User))
    users = result.scalars().all()

    migrated_count = 0
    total_records = 0

    for user in users:
        user_migrated = False
        logger.info(f"Processing user {user.id} (@{user.username})")

        # Process free mode kills
        if user.animals_killed_free:
            logger.info(f"User {user.id} has animals_killed_free: {user.animals_killed_free}")
            for animal_name, count in user.animals_killed_free.items():
                location = get_animal_location(animal_name)
                logger.info(f"Animal: {animal_name}, Location: {location}")
                if location:
                    # Check if already exists
                    existing = await session.execute(
                        select(AnimalSpecies).where(
                            and_(
                                AnimalSpecies.user_id == user.id,
                                AnimalSpecies.animal_name == animal_name,
                                AnimalSpecies.location == location
                            )
                        )
                    )
                    existing_record = existing.scalar_one_or_none()

                    if existing_record:
                        existing_record.total_killed += count
                    else:
                        new_record = AnimalSpecies(
                            user_id=user.id,
                            animal_name=animal_name,
                            location=location,
                            total_killed=count
                        )
                        session.add(new_record)
                        total_records += 1
                    user_migrated = True
                else:
                    logger.warning(f"Could not find location for animal: {animal_name}")

        # Process story mode kills
        if user.animals_killed_story:
            logger.info(f"User {user.id} has animals_killed_story: {user.animals_killed_story}")
            for animal_name, count in user.animals_killed_story.items():
                location = get_animal_location(animal_name)
                logger.info(f"Animal: {animal_name}, Location: {location}")
                if location:
                    # Check if already exists
                    existing = await session.execute(
                        select(AnimalSpecies).where(
                            and_(
                                AnimalSpecies.user_id == user.id,
                                AnimalSpecies.animal_name == animal_name,
                                AnimalSpecies.location == location
                            )
                        )
                    )
                    existing_record = existing.scalar_one_or_none()

                    if existing_record:
                        existing_record.total_killed += count
                    else:
                        new_record = AnimalSpecies(
                            user_id=user.id,
                            animal_name=animal_name,
                            location=location,
                            total_killed=count
                        )
                        session.add(new_record)
                        total_records += 1
                    user_migrated = True
                else:
                    logger.warning(f"Could not find location for animal: {animal_name}")

        # Mark user as migrated only if they had data
        if user_migrated:
            user.animal_species_migration_done = True
            migrated_count += 1
        else:
            # Mark as migrated even if no data to avoid re-checking
            user.animal_species_migration_done = True

    await session.commit()
    logger.info(f"AnimalSpecies migration completed. Migrated {migrated_count} users, created {total_records} records.")
    return True
