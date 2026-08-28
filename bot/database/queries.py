from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Inventory, Weapon, Quest, UserQuest, Animal, Trophy, AuctionLot, StarsTransaction
from datetime import datetime, timedelta
from bot.config import MAX_ENERGY, ENERGY_REGEN_PASSIVE


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str = None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            game_mode="free",
            location_progress={
                "forest": 0, "taiga": 0, "mountains": 0, "steppe": 0, 
                "desert": 0, "jungle": 0, "swamp": 0, "tundra": 0, 
                "savanna": 0, "ocean": 0, "deep_forest": 0, "volcano": 0
            }
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
        if username and user.username != username:
            user.username = username
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
    
    if item and item.quantity >= quantity:
        item.quantity -= quantity
        if item.quantity <= 0:
            await session.delete(item)
        await session.commit()
        return True
    return False


async def update_location_progress(session: AsyncSession, user: User, location: str, progress_add: float) -> User:
    if not user.location_progress:
        user.location_progress = {}
    
    current = user.location_progress.get(location, 0)
    new_progress = min(100, current + progress_add)
    user.location_progress[location] = new_progress
    
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


async def get_active_quests(session: AsyncSession, user_id: int) -> list[UserQuest]:
    result = await session.execute(
        select(UserQuest).where(
            and_(UserQuest.user_id == user_id, UserQuest.status == "active")
        )
    )
    return result.scalars().all()


async def get_available_quests(session: AsyncSession, user_level: int, location: str, user_id: int) -> list[Quest]:
    # Get quest IDs that user already has (active or completed)
    user_quests_result = await session.execute(
        select(UserQuest.quest_id).where(UserQuest.user_id == user_id)
    )
    taken_quest_ids = set(q[0] for q in user_quests_result.all())
    
    # Get available quests excluding already taken ones
    result = await session.execute(
        select(Quest).where(
            and_(
                Quest.required_level <= user_level,
                Quest.location == location,
                ~Quest.id.in_(taken_quest_ids) if taken_quest_ids else True
            )
        )
    )
    return result.scalars().all()
