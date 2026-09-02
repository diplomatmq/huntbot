import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from sqlalchemy.orm.attributes import flag_modified
from bot.database.db import async_session
from bot.database.queries import (
    get_or_create_user, update_energy, add_inventory_item,
    add_exp, add_coins, update_location_progress, add_species_kill, log_hunt,
    create_stars_transaction, update_stars_transaction
)
from bot.game_logic.animals import select_random_animal, calculate_rewards, generate_drops, drop_to_ru
from bot.game_logic.locations import get_location
from bot.keyboards.trap_kb import get_trap_payment_keyboard
from bot.utils.telegram_api import TelegramBotAPI
from bot.config import BOT_TOKEN

logger = logging.getLogger(__name__)

router = Router()

# Sticker directory
STICKERS_DIR = Path(__file__).parent.parent.parent / "stickers"

# Trap configurations
TRAP_CONFIGS = {
    1: {  # Капкан
        "name": "Капкан",
        "emoji": "🪤",
        "trigger_time_min": 30,  # minutes
        "animals_min": 1,
        "animals_max": 1,
        "cooldown_hours": 5,
        "skip_cost": 3  # stars
    },
    2: {  # Яма
        "name": "Яма",
        "emoji": "🕳️",
        "trigger_time_min": 20,  # minutes
        "animals_min": 2,
        "animals_max": 7,
        "cooldown_hours": 5,
        "skip_cost": 10  # stars
    },
    3: {  # Автоматический капкан
        "name": "Автоматический капкан",
        "emoji": "⚙️",
        "trigger_time_min": 10,  # minutes
        "animals_min": 8,
        "animals_max": 13,
        "cooldown_hours": 5,
        "skip_cost": 15  # stars
    }
}


async def can_use_trap(user) -> tuple[bool, str]:
    """Check if user can use trap"""
    if user.trap_active:
        return False, "❌ У вас уже установлена ловушка!"
    
    if user.last_trap_time:
        config = TRAP_CONFIGS[user.trap_level]
        cooldown_end = user.last_trap_time + timedelta(hours=config["cooldown_hours"])
        now = datetime.utcnow()
        
        if now < cooldown_end:
            remaining = cooldown_end - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            return False, f"⏳ Кулдаун: {hours} ч {minutes} мин. Пропустить за {config['skip_cost']} ⭐"
    
    return True, ""


async def activate_trap(user, session):
    """Activate user's trap"""
    # Consume energy
    from bot.database.queries import consume_energy
    if not await consume_energy(session, user, 13):
        return None
    
    config = TRAP_CONFIGS[user.trap_level]
    
    # Set trap as active
    user.trap_active = True
    user.trap_set_time = datetime.utcnow()
    
    await session.commit()
    await session.refresh(user)
    
    return config


async def check_and_trigger_trap(user, session):
    """Check if trap should trigger and process the catch"""
    if not user.trap_active or not user.trap_set_time:
        return None
    
    config = TRAP_CONFIGS[user.trap_level]
    trigger_time = user.trap_set_time + timedelta(minutes=config["trigger_time_min"])
    now = datetime.utcnow()
    
    if now >= trigger_time:
        # Trigger trap!
        return await trigger_trap_catch(user, session, config)
    
    return None


async def trigger_trap_catch(user, session, config):
    """Process trap catch"""
    # Deactivate trap
    user.trap_active = False
    user.last_trap_time = datetime.utcnow()
    
    # Determine number of animals caught
    num_animals = random.randint(config["animals_min"], config["animals_max"])
    
    location = get_location(user.current_location)
    caught_animals = []
    total_exp = 0
    total_coins = 0
    all_drops = {}
    
    for i in range(num_animals):
        # Select random animal from current location
        animal = select_random_animal(user.current_location, track_buff=False, bait_type=None)
        
        # Generate weight
        weight = round(random.uniform(animal.min_weight, animal.max_weight), 1)
        
        # Calculate rewards
        exp, coins = calculate_rewards(animal, weight)
        drops = generate_drops(animal)
        
        total_exp += exp
        total_coins += coins
        
        # Merge drops
        for item_name, quantity in drops.items():
            if item_name in all_drops:
                all_drops[item_name] += quantity
            else:
                all_drops[item_name] = quantity
        
        # Add drops to inventory (excluding quest items)
        quest_items = {"шкура", "когти", "рога", "клыки", "перья", "раковина", "яд", "бивни"}
        for item_name, quantity in drops.items():
            if item_name.lower() in quest_items:
                continue
            item_type = "meat" if item_name.lower() == "мясо" else "material"
            await add_inventory_item(session, user.id, item_name, item_type, quantity, animal.rarity)
        
        # Add to species kill count
        await add_species_kill(session, user.id, animal.name, user.current_location, 1)
        
        # Log the hunt
        await log_hunt(
            session, user.id, animal.name, animal.emoji, user.current_location,
            animal.rarity, weight, exp, coins, drops, True, user.game_mode
        )
        
        caught_animals.append({
            "animal": animal,
            "weight": weight,
            "exp": exp,
            "coins": coins,
            "drops": drops
        })
    
    # Add total rewards to user
    user = await add_exp(session, user, total_exp)
    user = await add_coins(session, user, total_coins)
    
    # Update location progress
    progress_add = 0.5 * num_animals if user.game_mode == "free" else 1.0 * num_animals
    user = await update_location_progress(session, user, user.current_location, progress_add)
    
    await session.commit()
    await session.refresh(user)
    
    return {
        "num_animals": num_animals,
        "caught_animals": caught_animals,
        "total_exp": total_exp,
        "total_coins": total_coins,
        "all_drops": all_drops,
        "location": location,
        "user": user
    }


@router.message(lambda msg: msg.text and msg.text.lower().strip() == "ловушка")
async def cmd_trap(message: Message):
    """Command to set a trap"""
    logger.info(f"[TRAP] User {message.from_user.id} (@{message.from_user.username}) used command: ловушка")
    
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user = await update_energy(session, user)
        
        # Check if trap can trigger first
        trap_result = await check_and_trigger_trap(user, session)
        if trap_result:
            # Trap triggered! Send results
            await send_trap_results(message, trap_result)
            return
        
        # Check if can use trap
        can_use, error_msg = await can_use_trap(user)
        
        if not can_use:
            # Check if it's a cooldown error
            if "Кулдаун" in error_msg:
                config = TRAP_CONFIGS[user.trap_level]
                # Create payment link for skipping cooldown
                telegram_api = TelegramBotAPI(BOT_TOKEN)
                timestamp = int(datetime.now().timestamp())
                payload = f"skip_trap_cooldown_{message.from_user.id}_{timestamp}"
                invoice_link = await telegram_api.create_invoice_link(
                    title=f"Пропустить кулдаун ловушки",
                    description=f"Пропустить кулдаун и установить {config['name']}",
                    payload=payload,
                    currency="XTR",
                    prices=[{"label": "Пропустить кулдаун", "amount": config["skip_cost"]}],
                    provider_token=None
                )
                
                # Log transaction
                await create_stars_transaction(
                    session,
                    user.id,
                    payload,
                    invoice_link,
                    config["skip_cost"],
                    message_id=message.message_id,
                    chat_id=message.chat.id
                )
                
                await message.answer(
                    error_msg,
                    reply_markup=get_trap_payment_keyboard(invoice_link, config["skip_cost"]),
                    reply_to_message_id=message.message_id
                )
            else:
                await message.answer(error_msg, reply_to_message_id=message.message_id)
            return
        
        # Activate trap
        config = await activate_trap(user, session)
        
        trigger_time = user.trap_set_time + timedelta(minutes=config["trigger_time_min"])
        
        await message.answer(
            f"{config['emoji']} <b>{config['name']} установлена!</b>\n\n"
            f"⏰ Сработает в течение {config['trigger_time_min']} минут\n"
            f"🎯 Поймает от {config['animals_min']} до {config['animals_max']} животных\n\n"
            f"💡 Используйте команду <b>ловушка</b> после срабатывания, чтобы получить добычу!",
            reply_to_message_id=message.message_id
        )


async def send_trap_results(message: Message, trap_result):
    """Send trap catch results to user"""
    num_animals = trap_result["num_animals"]
    caught_animals = trap_result["caught_animals"]
    total_exp = trap_result["total_exp"]
    total_coins = trap_result["total_coins"]
    all_drops = trap_result["all_drops"]
    location = trap_result["location"]
    user = trap_result["user"]
    
    rarity_emoji = {
        "common": "⚪",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡"
    }
    
    # Format animals list
    animals_text = ""
    for i, catch in enumerate(caught_animals, 1):
        animal = catch["animal"]
        weight = catch["weight"]
        animals_text += f"{i}. {rarity_emoji.get(animal.rarity, '⚪')} {animal.emoji} {animal.name} ({weight} кг)\n"
    
    # Format drops
    drops_by_type = {}
    for item, quantity in all_drops.items():
        ru_name = drop_to_ru(item)
        if ru_name not in drops_by_type:
            drops_by_type[ru_name] = 0
        drops_by_type[ru_name] += quantity
    
    drops_lines = []
    for item_name, total_qty in sorted(drops_by_type.items()):
        drops_lines.append(f"• {total_qty}x {item_name}")
    drops_text = "\n".join(drops_lines) if drops_lines else "Нет добычи"
    
    config = TRAP_CONFIGS[user.trap_level]
    
    await message.answer(
        f"🎉 <b>Ловушка сработала!</b>\n\n"
        f"{config['emoji']} <b>{config['name']}</b>\n"
        f"🦌 Поймано животных: {num_animals}\n\n"
        f"{animals_text}\n"
        f"📊 Общие награды:\n"
        f"• +{total_exp} опыта\n"
        f"• +{total_coins} монет\n\n"
        f"Добыча:\n{drops_text}\n\n"
        f"📍 Локация: {location.emoji} {location.name}\n"
        f"⚡ Энергия: {user.energy}/{user.max_energy}",
        reply_to_message_id=message.message_id
    )


# Payment handlers
from aiogram.types import PreCheckoutQuery
from sqlalchemy import select, and_
from bot.database.models import StarsTransaction

paid_trap_payloads = set()
PAID_TRAP_PAYLOADS_MAX = 1000


@router.pre_checkout_query(F.invoice_payload.startswith("skip_trap_cooldown_"))
async def process_pre_checkout_query_trap(pre_checkout_query: PreCheckoutQuery):
    """Pre-checkout handler for trap cooldown skip payments"""
    payload = pre_checkout_query.invoice_payload
    telegram_user_id = pre_checkout_query.from_user.id

    async with async_session() as session:
        # Get user by telegram_id
        user = await get_or_create_user(session, telegram_user_id, pre_checkout_query.from_user.username)
        
        # Check transaction in database
        result = await session.execute(
            select(StarsTransaction).where(
                and_(
                    StarsTransaction.invoice_payload == payload,
                    StarsTransaction.status == "pending"
                )
            ).order_by(StarsTransaction.created_at.desc()).limit(1)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            await pre_checkout_query.answer(ok=False, error_message="Инвойс не найден. Запросите новый.")
            return

        # Check if transaction belongs to this user
        if transaction.user_id != user.id:
            await pre_checkout_query.answer(ok=False, error_message="Этот инвойс создан для другого пользователя.")
            return

        # Check if already paid
        if payload in paid_trap_payloads:
            await pre_checkout_query.answer(ok=False, error_message="Этот инвойс уже оплачен.")
            return

        # Check if invoice is expired (15 minutes)
        now_ts = int(datetime.now().timestamp())
        parts = payload.split("_")
        try:
            timestamp = int(parts[-1])
            if now_ts - timestamp > 900:
                await pre_checkout_query.answer(ok=False, error_message="Срок действия инвойса истек. Запросите новый.")
                return
        except (ValueError, IndexError):
            pass

        await pre_checkout_query.answer(ok=True)


async def handle_trap_payment(message: Message, payload: str, telegram_payment_id: str):
    """Handle successful trap cooldown skip payment"""
    global paid_trap_payloads
    
    # Protection against duplicate payments
    if payload in paid_trap_payloads:
        return
    
    # Mark payload as paid
    if len(paid_trap_payloads) >= PAID_TRAP_PAYLOADS_MAX:
        old_entries = list(paid_trap_payloads)
        paid_trap_payloads = set(old_entries[len(old_entries)//2:])
    paid_trap_payloads.add(payload)
    
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        
        # Find and update transaction
        result = await session.execute(
            select(StarsTransaction).where(
                and_(
                    StarsTransaction.user_id == user.id,
                    StarsTransaction.invoice_payload == payload,
                    StarsTransaction.status == "pending"
                )
            ).order_by(StarsTransaction.created_at.desc()).limit(1)
        )
        transaction = result.scalar_one_or_none()
        
        reply_to_id = transaction.message_id if transaction else None
        
        if transaction:
            await update_stars_transaction(
                session,
                transaction.id,
                "completed",
                telegram_payment_id=telegram_payment_id
            )
        
        # Activate trap (skip cooldown)
        config = await activate_trap(user, session)
        
        trigger_time = user.trap_set_time + timedelta(minutes=config["trigger_time_min"])
        
        await message.answer(
            f"✅ <b>Оплата успешна!</b>\n\n"
            f"{config['emoji']} <b>{config['name']} установлена!</b>\n\n"
            f"⏰ Сработает в течение {config['trigger_time_min']} минут\n"
            f"🎯 Поймает от {config['animals_min']} до {config['animals_max']} животных\n\n"
            f"💡 Используйте команду <b>ловушка</b> после срабатывания, чтобы получить добычу!",
            reply_to_message_id=reply_to_id
        )
