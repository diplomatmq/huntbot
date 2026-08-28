import random
import logging
from pathlib import Path
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, PreCheckoutQuery, SuccessfulPayment
from sqlalchemy import select, and_
from bot.database.db import async_session
from bot.database.models import StarsTransaction, Inventory
from bot.database.queries import (
    get_or_create_user, update_energy, consume_energy, can_hunt,
    update_hunt_cooldown, add_inventory_item, update_location_progress,
    add_exp, add_coins, add_energy, get_equipped_weapon, get_active_quests,
    create_stars_transaction, update_stars_transaction, consume_inventory_item
)
from bot.game_logic.animals import select_random_animal, calculate_rewards, generate_drops, can_kill_animal
from bot.game_logic.hunt_calculator import calculate_hit_chance
from bot.game_logic.locations import get_location
from bot.keyboards.hunt_kb import (
    get_bait_keyboard,
    get_hunt_keyboard,
    get_guaranteed_hit_keyboard,
    get_skip_cooldown_keyboard
)
from bot.utils.telegram_api import TelegramBotAPI
from bot.config import HUNT_COOLDOWN, BOT_TOKEN

logger = logging.getLogger(__name__)

router = Router()

# Sticker directory
STICKERS_DIR = Path(__file__).parent.parent.parent / "stickers"

# Protection against duplicate payments
paid_payloads = set()
PAID_PAYLOADS_MAX = 1000


async def perform_hunt_logic(session, user, message_obj, telegram_user_id, is_guaranteed=False, reply_to_message_id=None):
    """Reusable hunt logic that works for both normal and guaranteed hits"""
    logger.info(f"[HUNT] User {user.telegram_id} (@{user.username}) started {'guaranteed' if is_guaranteed else 'normal'} hunt at location {user.current_location}")

    # Consume energy only for normal hunts (guaranteed hunts are paid with stars)
    if not is_guaranteed:
        energy_cost = 5
        if not await consume_energy(session, user, energy_cost):
            await message_obj.answer("❌ Недостаточно энергии!", reply_to_message_id=reply_to_message_id)
            logger.warning(f"[HUNT] User {user.telegram_id} failed hunt: not enough energy")
            return
    
    # Get equipped weapon
    weapon = await get_equipped_weapon(session, user.id)
    weapon_type = weapon.weapon_type if weapon else "bow"
    weapon_durability = weapon.durability if weapon else 100
    
    track_buff = user.active_buffs.get("track", {}).get("active", False)
    track_bonus = user.active_buffs.get("track", {}).get("bonus", 0)
    ambush_buff = user.active_buffs.get("ambush", {}).get("active", False)
    bait_type = user.active_buffs.get("bait", {}).get("type")
    
    is_hit = True if is_guaranteed else False
    if not is_guaranteed:
        # Calculate hit chance only for normal hunts
        accuracy_skill = user.skills.get("accuracy", 0)
        hit_chance = calculate_hit_chance(
            accuracy_skill=accuracy_skill,
            weapon_type=weapon_type,
            weapon_durability=weapon_durability,
            track_buff=track_buff,
            track_bonus=track_bonus,
            ambush_buff=ambush_buff
        )
        # Roll for hit
        roll = random.randint(1, 100)
        is_hit = roll <= hit_chance
    
    # Clear track buff after use (it's only for one hunt)
    if track_buff:
        user.active_buffs.pop("track", None)
    if bait_type:
        user.active_buffs.pop("bait", None)
    user.track_uses = 0
    await session.commit()

    location = get_location(user.current_location)
    
    if is_hit:
        logger.info(f"[HUNT] User {user.telegram_id} (@{user.username}) HIT!")
        
        # Select animal with higher chance for rare animals if guaranteed
        if is_guaranteed:
            # For guaranteed hunts, increase rare animal chances significantly
            animal = select_random_animal(user.current_location, track_buff=True, bait_type=bait_type)
        else:
            animal = select_random_animal(user.current_location, track_buff, bait_type)
        
        # Check if weapon can kill the animal (skip for guaranteed hunts)
        if not is_guaranteed:
            killed, kill_chance = can_kill_animal(weapon_type, animal)
            
            if not killed:
                # Animal wounded but not killed
                logger.info(f"[HUNT] User {user.telegram_id} (@{user.username}) WOUNDED {animal.name}")
                
                # Update statistics based on mode
            if user.game_mode == "free":
                user.total_hunts_free += 1
            else:
                user.total_hunts_story += 1
            
            # Reset track uses after wound
            user.track_uses = 0
            
            # Commit changes
            await session.commit()
            
            # Update cooldown
            user = await update_hunt_cooldown(session, user)
            
            # Small exp reward for wounding
            exp_reward = 5
            user = await add_exp(session, user, exp_reward)
            
            rarity_emoji = {
                "common": "⚪",
                "uncommon": "🟢",
                "rare": "🔵",
                "epic": "🟣",
                "legendary": "🟡"
            }
            
            await message_obj.answer(
                f"💔 <b>Ранено!</b>\n\n"
                f"{rarity_emoji.get(animal.rarity, '⚪')} {animal.emoji} <b>{animal.name}</b>\n"
                f"Редкость: {animal.rarity}\n\n"
                f"Ваше оружие ({weapon_type}) не смогло убить животное!\n"
                f"Животное ранено и сбежало...\n\n"
                f"💡 Шанс убийства: {int(kill_chance * 100)}%\n"
                f"📊 +{exp_reward} опыта за попытку\n\n"
                f"📍 Локация: {location.emoji} {location.name}\n"
                f"⚡ Энергия: {user.energy}/{user.max_energy}",
                reply_to_message_id=reply_to_message_id
            )
            return
        
        # Animal killed
        logger.info(f"[HUNT] User {user.telegram_id} (@{user.username}) KILLED {animal.name}")
        
        # Generate weight
        weight = round(random.uniform(animal.min_weight, animal.max_weight), 1)
        
        # Calculate rewards
        exp, coins = calculate_rewards(animal, weight)
        drops = generate_drops(animal)
        
        # Add rewards to user
        user = await add_exp(session, user, exp)
        user = await add_coins(session, user, coins)
        
        # Add drops to inventory
        for item_name, quantity in drops.items():
            item_type = "meat" if item_name == "meat" else "material"
            await add_inventory_item(session, user.id, item_name, item_type, quantity, animal.rarity)
        
        # Update statistics based on mode
        animal_name_key = animal.name.lower()
        quest_progress_text = ""
        completed_quests = []

        if user.game_mode == "free":
            user.total_hunts_free += 1
            user.successful_hunts_free += 1
            user.animals_killed_free[animal_name_key] = user.animals_killed_free.get(animal_name_key, 0) + 1
        else:
            user.total_hunts_story += 1
            user.successful_hunts_story += 1
            user.animals_killed_story[animal_name_key] = user.animals_killed_story.get(animal_name_key, 0) + 1

            # Update quest progress and check for completion
            active_quests = await get_active_quests(session, user.id)

            for uq in active_quests:
                quest = uq.quest
                if quest.conditions.get("kill"):
                    target_animal = quest.conditions["kill"]["animal"]
                    required_count = quest.conditions["kill"]["count"]
                    if animal.name == target_animal:
                        uq.progress["killed"] = uq.progress.get("killed", 0) + 1
                        current_killed = uq.progress["killed"]
                        remaining = required_count - current_killed

                        if remaining > 0:
                            quest_progress_text += f"\n📜 Квест: {quest.title}\n   Осталось словить: {remaining} {target_animal}\n"
                        else:
                            # Quest completed
                            uq.status = "completed"
                            uq.completed_at = datetime.utcnow()
                            completed_quests.append(quest)

                            # Give quest rewards
                            user = await add_exp(session, user, quest.reward_exp)
                            user = await add_coins(session, user, quest.reward_coins)
                            user.stars += quest.reward_stars

                            # Add reward items
                            for reward_item in quest.reward_items:
                                item_name = reward_item["item"]
                                quantity = reward_item["quantity"]
                                await add_inventory_item(session, user.id, item_name, "material", quantity)

                            # Update location progress
                            user = await update_location_progress(session, user, quest.location, quest.progress_reward)
        
        # Commit changes after modifying user stats/quests
        await session.commit()
        await session.refresh(user)
        
        # Update location progress (in both modes)
        old_progress = user.location_progress.get(user.current_location, 0)
        progress_add = 0.5 if user.game_mode == "free" else 1.0  # Story mode gives more progress
        user = await update_location_progress(session, user, user.current_location, progress_add)
        new_progress = user.location_progress.get(user.current_location, 0)
        
        # Check if new location unlocked in story mode
        new_location_unlocked = None
        if user.game_mode == "story":
            from bot.game_logic.locations import get_all_locations, can_unlock_location
            for loc in get_all_locations():
                if loc.required_progress == user.current_location:
                    # Check if this location just became unlocked
                    if old_progress < loc.progress_threshold <= new_progress:
                        new_location_unlocked = loc
                        break
        
        # Update cooldown
        user = await update_hunt_cooldown(session, user)
        
        # Format drops text
        drops_text = "\n".join([f"• {quantity}x {item}" for item, quantity in drops.items()])
        
        rarity_emoji = {
            "common": "⚪",
            "uncommon": "🟢",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟡"
        }
        
        # Send sticker if exists (as reply to original message)
        sticker_path = STICKERS_DIR / animal.sticker_file
        if sticker_path.exists():
            await message_obj.answer_document(FSInputFile(sticker_path), reply_to_message_id=reply_to_message_id)
        
        # Build progress text
        progress_text = ""
        if user.game_mode == "story":
            progress_text = f"\n📈 Прогресс локации: {new_progress:.1f}%"
        
        # Build new location unlock text
        unlock_text = ""
        if new_location_unlocked:
            unlock_text = f"\n\n🎉 <b>Открыта новая локация: {new_location_unlocked.emoji} {new_location_unlocked.name}!</b>"
        
        title = f"🎯 <b>{'Гарантированное попадание!' if is_guaranteed else 'Попадание!'}</b>\n\n"
        await message_obj.answer(
            title +
            f"{rarity_emoji.get(animal.rarity, '⚪')} {animal.emoji} <b>{animal.name}</b>\n"
            f"Вес: {weight} кг\n"
            f"Редкость: {animal.rarity}\n\n"
            f"📊 Награды:\n"
            f"• +{exp} опыта\n"
            f"• +{coins} монет\n"
            f"Добыча:\n{drops_text}\n\n"
            f"📍 Локация: {location.emoji} {location.name}{progress_text}\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}"
            f"{quest_progress_text}{unlock_text}",
            reply_to_message_id=reply_to_message_id
        )

        # Send completion messages for completed quests
        for quest in completed_quests:
            await message_obj.answer(
                f"🎉 <b>Квест выполнен!</b>\n\n"
                f"📜 {quest.title}\n"
                f"{quest.description}\n\n"
                f"🎁 Награды:\n"
                f"• +{quest.reward_exp} опыта\n"
                f"• +{quest.reward_coins} монет\n"
                f"• +{quest.reward_stars} звёзд",
                reply_to_message_id=reply_to_message_id
            )
    else:
        # This should never happen for guaranteed hunts
        if not is_guaranteed:
            logger.info(f"[HUNT] User {user.telegram_id} (@{user.username}) MISS!")
            # Update statistics based on mode
            if user.game_mode == "free":
                user.total_hunts_free += 1
            else:
                user.total_hunts_story += 1

            # Reset track uses after miss
            user.track_uses = 0

            # Commit changes
            await session.commit()

            # Update cooldown
            user = await update_hunt_cooldown(session, user)

            # Create invoice link for guaranteed hit
            telegram_api = TelegramBotAPI(BOT_TOKEN)
            star_cost = 2 if user.game_mode == "story" else 1
            timestamp = int(datetime.now().timestamp())
            payload = f"guaranteed_{telegram_user_id}_{timestamp}"
            invoice_link = await telegram_api.create_invoice_link(
                title="Гарантированное попадание",
                description="Гарантированное попадание на следующей охоте",
                payload=payload,
                currency="XTR",
                prices=[{"label": "Гарантированное попадание", "amount": star_cost}],
                provider_token=None
            )

            # Log transaction with message_id for reply
            transaction = await create_stars_transaction(
                session,
                user.id,
                payload,
                invoice_link,
                star_cost,
                message_id=message_obj.message_id if hasattr(message_obj, 'message_id') else None,
                chat_id=message_obj.chat.id if hasattr(message_obj, 'chat') else None
            )

            await message_obj.answer(
                f"❌ <b>Ой, неудача...</b>\n\n"
                f"+5 опыта за попытку\n\n"
                f"📍 Локация: {location.emoji} {location.name}\n"
                f"⚡ Энергия: {user.energy}/{user.max_energy}",
                reply_markup=get_guaranteed_hit_keyboard(invoice_link, star_cost),
                reply_to_message_id=reply_to_message_id
            )


@router.message(lambda msg: msg.text and msg.text.split()[0].lower() in ["хант", "выстрел", "hunt"])
async def cmd_hunt(message: Message):
    logger.info(f"[CMD] User {message.from_user.id} (@{message.from_user.username}) used command: {message.text}")
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user = await update_energy(session, user)
        
        can_hunt_result, error_msg, cooldown_minutes, cooldown_seconds = await can_hunt(user)
        if not can_hunt_result:
            star_cost = 2 if user.game_mode == "story" else 1
            telegram_api = TelegramBotAPI(BOT_TOKEN)
            timestamp = int(datetime.now().timestamp())
            payload = f"skip_cooldown_{message.from_user.id}_{timestamp}"
            invoice_link = await telegram_api.create_invoice_link(
                title="Гарантированное попадание",
                description="Пропустить кулдаун и сделать гарантированную охоту",
                payload=payload,
                currency="XTR",
                prices=[{"label": "Гарантированное попадание", "amount": star_cost}],
                provider_token=None
            )

            # Log transaction with message_id for reply
            transaction = await create_stars_transaction(
                session,
                user.id,
                payload,
                invoice_link,
                star_cost,
                message_id=message.message_id,
                chat_id=message.chat.id
            )

            await message.answer(
                f"⏳ <b>Время до следующего выстрела: {cooldown_minutes} мин {cooldown_seconds} сек</b>\n\n"
                f"💫 Оплатите {star_cost} ⭐ чтобы пропустить кулдаун и сделать гарантированную охоту!",
                reply_markup=get_skip_cooldown_keyboard(invoice_link, star_cost),
                reply_to_message_id=message.message_id
            )
            return
        
        await perform_hunt_logic(session, user, message, message.from_user.id, is_guaranteed=False, reply_to_message_id=message.message_id)


@router.message(lambda msg: msg.text and msg.text.split()[0].lower() == "след")
async def cmd_track(message: Message):
    logger.info(f"[CMD] User {message.from_user.id} (@{message.from_user.username}) used command: {message.text}")
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user = await update_energy(session, user)

        # Check if user already used "след" without hunting
        if user.track_uses >= 1:
            await message.answer("❌ Вы уже использовали команду 'след'. Сначала совершите охоту!", reply_to_message_id=message.message_id)
            return

        energy_cost = 3
        if user.energy < energy_cost:
            await message.answer("❌ Недостаточно энергии! (нужно 3)", reply_to_message_id=message.message_id)
            return

        if not await consume_energy(session, user, energy_cost):
            await message.answer("❌ Недостаточно энергии!", reply_to_message_id=message.message_id)
            return

        # Random bonus from -5 to 20
        bonus = random.randint(-5, 20)

        # Activate track buff (only for next hunt)
        user.active_buffs["track"] = {"active": True, "bonus": bonus}

        # Increment track uses
        user.track_uses += 1
        
        # Commit the changes to the database
        await session.commit()

        if bonus > 0:
            await message.answer(
                f"👣 <b>Вы нашли следы!</b>\n\n"
                f"Следующая охота имеет +{bonus}% шанс на редкое животное.\n\n"
                f"⚡ Энергия: {user.energy}/{user.max_energy}",
                reply_to_message_id=message.message_id
            )
        elif bonus == 0:
            await message.answer(
                f"👣 <b>Вы нашли следы...</b>\n\n"
                f"Следы не дали никакой информации. Шанс не изменён.\n\n"
                f"⚡ Энергия: {user.energy}/{user.max_energy}",
                reply_to_message_id=message.message_id
            )
        else:
            await message.answer(
                f"👣 <b>Вы упали лицом в грязь!</b>\n\n"
                f"Следующая охота имеет {bonus}% шанс на редкое животное.\n\n"
                f"⚡ Энергия: {user.energy}/{user.max_energy}",
                reply_to_message_id=message.message_id
            )


@router.message(lambda msg: msg.text and msg.text.split()[0].lower() == "приманка")
async def cmd_bait(message: Message):
    logger.info(f"[CMD] User {message.from_user.id} (@{message.from_user.username}) used command: {message.text}")
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user = await update_energy(session, user)

        result = await session.execute(
            select(Inventory).where(
                and_(
                    Inventory.user_id == user.id,
                    Inventory.item_type == "bait",
                    Inventory.quantity > 0
                )
            ).order_by(Inventory.item_name)
        )
        bait_items = result.scalars().all()

        if not bait_items:
            await message.answer("❌ У вас нет приманки! Купите её в магазине.", reply_to_message_id=message.message_id)
            return

        baits = [
            {"id": item.id, "name": item.item_name, "quantity": item.quantity}
            for item in bait_items
        ]
        await message.answer(
            "🍖 <b>Выберите приманку</b>\n\n"
            "После выбора она сразу активируется и потратит 4 энергии.",
            reply_markup=get_bait_keyboard(baits),
            reply_to_message_id=message.message_id
        )


@router.callback_query(F.data.startswith("use_bait_"))
async def use_bait(callback: CallbackQuery):
    bait_id = int(callback.data.split("_")[-1])
    logger.info(f"[CMD] User {callback.from_user.id} (@{callback.from_user.username}) selected bait id={bait_id}")

    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)

        energy_cost = 4
        if user.energy < energy_cost:
            await callback.answer("❌ Недостаточно энергии! Нужно 4.", show_alert=True)
            return

        result = await session.execute(
            select(Inventory).where(
                and_(
                    Inventory.id == bait_id,
                    Inventory.user_id == user.id,
                    Inventory.item_type == "bait"
                )
            )
        )
        bait_item = result.scalar_one_or_none()

        if not bait_item or bait_item.quantity <= 0:
            await callback.answer("❌ Эта приманка не найдена.", show_alert=True)
            return

        bait_name = bait_item.item_name.lower().replace("_", " ")
        if "травояд" in bait_name:
            bait_type = "herbivore"
        elif "хищ" in bait_name:
            bait_type = "predator"
        else:
            await callback.answer("❌ Не удалось определить тип приманки.", show_alert=True)
            return

        user.energy -= energy_cost
        user.active_buffs["bait"] = {"type": bait_type}
        bait_item.quantity -= 1

        if bait_item.quantity <= 0:
            await session.delete(bait_item)

        await session.commit()

        display_name = bait_name.capitalize()
        await callback.message.edit_text(
            f"🍖 <b>Приманка активирована</b>\n\n"
            f"Вы выбрали: {display_name}\n"
            f"Следующая охота гарантированно даст животное выбранного типа.\n\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}"
        )
        await callback.answer("✅ Приманка активирована!")


@router.message(lambda msg: msg.text and msg.text.split()[0].lower() == "засада")
async def cmd_ambush(message: Message):
    logger.info(f"[CMD] User {message.from_user.id} (@{message.from_user.username}) used command: {message.text}")
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user = await update_energy(session, user)
        
        energy_cost = 6
        if user.energy < energy_cost:
            await message.answer("❌ Недостаточно энергии! (нужно 6)", reply_to_message_id=message.message_id)
            return
        
        if not await consume_energy(session, user, energy_cost):
            await message.answer("❌ Недостаточно энергии!", reply_to_message_id=message.message_id)
            return
        
        # Activate ambush buff (3 uses)
        user.active_buffs["ambush"] = {"active": True, "count": 3}
        
        # Commit changes
        await session.commit()
        
        await message.answer(
            f"🌲 <b>Вы устроили засаду!</b>\n\n"
            f"+30% к шансу крупной добычи на следующие 3 охоты.\n\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}",
            reply_to_message_id=message.message_id
        )


@router.message(lambda msg: msg.text and msg.text.split()[0].lower() == "отдых")
async def cmd_rest(message: Message):
    logger.info(f"[CMD] User {message.from_user.id} (@{message.from_user.username}) used command: {message.text}")
    parts = message.text.split()
    portions = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        
        # Check if user has meat
        has_meat = await consume_inventory_item(session, user.id, "мясо", "meat", portions)
        if not has_meat:
            await message.answer(f"❌ У вас нет мяса! Нужно {portions} порций.", reply_to_message_id=message.message_id)
            return
        
        # Add energy
        energy_gain = portions * 20
        user = await add_energy(session, user, energy_gain)
        
        await message.answer(
            f"😴 <b>Вы отдохнули и съели {portions} порций мяса.</b>\n\n"
            f"+{energy_gain} энергии\n\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}",
            reply_to_message_id=message.message_id
        )


@router.callback_query(F.data == "hunt")
async def callback_hunt(callback: CallbackQuery):
    await callback.answer()
    # Create a dummy message-like object with answer method and from_user
    class DummyMessage:
        def __init__(self, callback):
            self.from_user = callback.from_user
            self.answer = callback.message.answer
            self.answer_document = callback.message.answer_document
            self.message_id = callback.message.message_id
    
    await cmd_hunt(DummyMessage(callback))


@router.callback_query(F.data == "skip_cooldown")
async def skip_cooldown(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)

        if user.stars < 1:
            await callback.answer("❌ Недостаточно звёзд!", show_alert=True)
            return

        user.stars -= 1
        user.last_hunt_time = None
        await session.commit()

        await callback.answer("✅ Кулдаун пропущен!")
        await callback.message.edit_reply_markup(reply_markup=get_hunt_keyboard())


@router.pre_checkout_query(F.invoice_payload.startswith("guaranteed_"))
async def process_pre_checkout_query_guaranteed(pre_checkout_query: PreCheckoutQuery):
    payload = pre_checkout_query.invoice_payload
    telegram_user_id = pre_checkout_query.from_user.id

    async with async_session() as session:
        # Get user by telegram_id
        user = await get_or_create_user(session, telegram_user_id, pre_checkout_query.from_user.username)
        user = await update_energy(session, user)
        
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

        # Check if transaction exists and belongs to this user
        if not transaction:
            await pre_checkout_query.answer(ok=False, error_message="Инвойс не найден. Запросите новый.")
            return

        if transaction.user_id != user.id:
            await pre_checkout_query.answer(ok=False, error_message="Этот инвойс создан для другого пользователя.")
            return

        # Check if already paid
        if payload in paid_payloads:
            await pre_checkout_query.answer(ok=False, error_message="Этот инвойс уже оплачен.")
            return

        # Check if invoice is expired (15 minutes)
        now_ts = int(datetime.now().timestamp())
        # Extract timestamp from payload
        parts = payload.split("_")
        try:
            timestamp = int(parts[2])
            if now_ts - timestamp > 900:
                await pre_checkout_query.answer(ok=False, error_message="Срок действия инвойса истек. Запросите новый.")
                return
        except (ValueError, IndexError):
            pass  # Skip timestamp check if can't parse

        # Check if user can hunt (energy and cooldown)
        can_hunt_result, error_msg, cooldown_minutes, cooldown_seconds = await can_hunt(user)

        if not can_hunt_result:
            # Reject payment if user can't hunt
            await pre_checkout_query.answer(
                ok=False,
                error_message=f"Невозможно выполнить гарантированную охоту: {error_msg}"
            )

            # Log failed transaction
            await update_stars_transaction(
                session,
                transaction.id,
                "failed",
                error_message=error_msg
            )
            return

        await pre_checkout_query.answer(ok=True)


@router.pre_checkout_query(F.invoice_payload.startswith("skip_cooldown_"))
async def process_pre_checkout_query_skip(pre_checkout_query: PreCheckoutQuery):
    payload = pre_checkout_query.invoice_payload
    telegram_user_id = pre_checkout_query.from_user.id

    async with async_session() as session:
        # Get user by telegram_id
        user = await get_or_create_user(session, telegram_user_id, pre_checkout_query.from_user.username)
        user = await update_energy(session, user)
        
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

        # Check if transaction exists and belongs to this user
        if not transaction:
            await pre_checkout_query.answer(ok=False, error_message="Инвойс не найден. Запросите новый.")
            return

        if transaction.user_id != user.id:
            await pre_checkout_query.answer(ok=False, error_message="Этот инвойс создан для другого пользователя.")
            return

        # Check if already paid
        if payload in paid_payloads:
            await pre_checkout_query.answer(ok=False, error_message="Этот инвойс уже оплачен.")
            return

        # Check if invoice is expired (15 minutes)
        now_ts = int(datetime.now().timestamp())
        # Extract timestamp from payload: skip_cooldown_{user_id}_{timestamp}
        parts = payload.split("_")
        try:
            timestamp = int(parts[3])
            if now_ts - timestamp > 900:
                await pre_checkout_query.answer(ok=False, error_message="Срок действия инвойса истек. Запросите новый.")
                return
        except (ValueError, IndexError):
            pass  # Skip timestamp check if can't parse

        # Check if user has cooldown
        if not user.last_hunt_time:
            await pre_checkout_query.answer(
                ok=False,
                error_message="У вас нет активного кулдауна!"
            )

            # Log failed transaction
            await update_stars_transaction(
                session,
                transaction.id,
                "failed",
                error_message="No active cooldown"
            )
            return

        from datetime import timedelta
        cooldown_remaining = (user.last_hunt_time + timedelta(seconds=600)) - datetime.utcnow()
        if cooldown_remaining.total_seconds() <= 0:
            await pre_checkout_query.answer(
                ok=False,
                error_message="Ваш кулдаун уже истёк!"
            )

            # Log failed transaction
            await update_stars_transaction(
                session,
                transaction.id,
                "failed",
                error_message="Cooldown already expired"
            )
            return

        await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    successful_payment = message.successful_payment
    payload = successful_payment.invoice_payload
    star_cost = successful_payment.total_amount  # Telegram Stars are NOT in cents, they come as is
    telegram_payment_id = successful_payment.telegram_payment_charge_id

    logger.info(f"[PAYMENT] User {message.from_user.id} (@{message.from_user.username}) successful payment: payload={payload}, stars={star_cost}, payment_id={telegram_payment_id}")

    # Route to shop handler if it's a shop payment
    if payload.startswith("shop_"):
        logger.info(f"[PAYMENT] Routing to shop handler")
        from bot.handlers.shop import handle_shop_payment
        await handle_shop_payment(message, payload, telegram_payment_id)
        return

    logger.info(f"[PAYMENT] Processing hunt/cooldown payment")

    # Protection against duplicate payments
    if payload in paid_payloads:
        logger.warning(f"[PAYMENT] Duplicate payment ignored (in memory) for payload={payload}")
        return

    logger.info(f"[PAYMENT] Opening database session")

    async with async_session() as session:
        # Check if transaction already completed (in case of duplicate webhook call)
        result = await session.execute(
            select(StarsTransaction).where(
                and_(
                    StarsTransaction.invoice_payload == payload,
                    StarsTransaction.status == "completed"
                )
            ).limit(1)
        )
        completed_transaction = result.scalar_one_or_none()
        
        if completed_transaction:
            logger.warning(f"[PAYMENT] Duplicate payment ignored (in DB) for payload={payload}")
            return

        # Mark payload as paid in memory
        if len(paid_payloads) >= PAID_PAYLOADS_MAX:
            old_entries = list(paid_payloads)
            paid_payloads.clear()
            for entry in old_entries[len(old_entries)//2:]:
                paid_payloads.add(entry)
            logger.info(f"[PAYMENT] paid_payloads trimmed to {len(paid_payloads)} entries")
        paid_payloads.add(payload)
        
        logger.info(f"[PAYMENT] Getting user from database")
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user = await update_energy(session, user)

        # Find and update pending transaction
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

        # Get the original message_id and chat_id to reply to
        reply_to_id = transaction.message_id if transaction else None
        original_chat_id = transaction.chat_id if transaction else None
        
        logger.info(f"[PAYMENT] Transaction found: {transaction is not None}, reply_to_id: {reply_to_id}, chat_id: {original_chat_id}")

        if transaction:
            await update_stars_transaction(
                session,
                transaction.id,
                "completed",
                telegram_payment_id=telegram_payment_id
            )

        if payload.startswith("guaranteed_"):
            logger.info(f"[PAYMENT] Starting guaranteed hunt for user {user.telegram_id}, reply_to={reply_to_id}")
            
            # Create a message-like object that sends to original chat
            class ChatMessage:
                def __init__(self, bot, chat_id, from_user):
                    self.bot = bot
                    self.chat_id = chat_id
                    self.from_user = from_user
                    self.chat = type('obj', (object,), {'id': chat_id})()
                    self.message_id = None
                
                async def answer(self, text, reply_to_message_id=None, reply_markup=None):
                    return await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=text,
                        reply_to_message_id=reply_to_message_id,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
                
                async def answer_document(self, document, reply_to_message_id=None):
                    return await self.bot.send_document(
                        chat_id=self.chat_id,
                        document=document,
                        reply_to_message_id=reply_to_message_id
                    )
            
            # Get bot instance from message
            bot = message.bot
            target_chat_id = original_chat_id if original_chat_id else message.chat.id
            chat_message = ChatMessage(bot, target_chat_id, message.from_user)
            
            try:
                await perform_hunt_logic(session, user, chat_message, message.from_user.id, is_guaranteed=True, reply_to_message_id=reply_to_id)
                logger.info(f"[PAYMENT] Guaranteed hunt completed successfully")
            except Exception as e:
                error_str = str(e)
                logger.error(f"[PAYMENT] Error in guaranteed hunt for user {user.telegram_id}: {e}", exc_info=True)

                # If error is about message not found, try without reply_to
                if "message to be replied not found" in error_str.lower():
                    try:
                        logger.info(f"[PAYMENT] Retrying hunt without reply_to_message_id")
                        await perform_hunt_logic(session, user, chat_message, message.from_user.id, is_guaranteed=True, reply_to_message_id=None)
                        logger.info(f"[PAYMENT] Guaranteed hunt completed (without reply)")
                        return
                    except Exception as e2:
                        logger.error(f"[PAYMENT] Failed even without reply: {e2}", exc_info=True)
                        error_str = str(e2)

                # Refund stars if error occurred
                user.stars += star_cost
                await session.commit()

                # Update transaction status to refunded
                if transaction:
                    await update_stars_transaction(
                        session,
                        transaction.id,
                        "refunded",
                        error_message=error_str
                    )
                
                logger.info(f"[PAYMENT] Refunded {star_cost} stars to user {user.telegram_id}")

                try:
                    await message.answer(
                        f"❌ <b>Произошла ошибка при выполнении гарантированной охоты</b>\n\n"
                        f"Ваши {star_cost} ⭐ возвращены."
                    )
                except Exception as e3:
                    logger.error(f"[PAYMENT] Failed to send refund message: {e3}", exc_info=True)
                return
        elif payload.startswith("skip_cooldown_"):
            # Reset cooldown and perform guaranteed hunt
            user.last_hunt_time = None
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"[PAYMENT] Cooldown skipped for user {user.telegram_id}, performing guaranteed hunt, reply_to={reply_to_id}")
            
            # Create a message-like object that sends to original chat
            class ChatMessage:
                def __init__(self, bot, chat_id, from_user):
                    self.bot = bot
                    self.chat_id = chat_id
                    self.from_user = from_user
                    self.chat = type('obj', (object,), {'id': chat_id})()
                    self.message_id = None
                
                async def answer(self, text, reply_to_message_id=None, reply_markup=None):
                    return await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=text,
                        reply_to_message_id=reply_to_message_id,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
                
                async def answer_document(self, document, reply_to_message_id=None):
                    return await self.bot.send_document(
                        chat_id=self.chat_id,
                        document=document,
                        reply_to_message_id=reply_to_message_id
                    )
            
            # Get bot instance from message
            bot = message.bot
            target_chat_id = original_chat_id if original_chat_id else message.chat.id
            chat_message = ChatMessage(bot, target_chat_id, message.from_user)
            
            # Perform guaranteed hunt after skipping cooldown
            try:
                # Try with reply first
                await perform_hunt_logic(session, user, chat_message, message.from_user.id, is_guaranteed=True, reply_to_message_id=reply_to_id)
                logger.info(f"[PAYMENT] Guaranteed hunt completed after skip_cooldown")
            except Exception as e:
                error_str = str(e)
                logger.error(f"[PAYMENT] Error in guaranteed hunt after skip_cooldown: {e}", exc_info=True)
                
                # If error is about message not found, try without reply_to
                if "message to be replied not found" in error_str.lower():
                    try:
                        logger.info(f"[PAYMENT] Retrying hunt without reply_to_message_id")
                        await perform_hunt_logic(session, user, chat_message, message.from_user.id, is_guaranteed=True, reply_to_message_id=None)
                        logger.info(f"[PAYMENT] Guaranteed hunt completed after skip_cooldown (without reply)")
                        return
                    except Exception as e2:
                        logger.error(f"[PAYMENT] Failed even without reply: {e2}", exc_info=True)
                
                # Refund stars if error occurred
                user.stars += star_cost
                await session.commit()
                
                # Update transaction to refunded
                if transaction:
                    await update_stars_transaction(
                        session,
                        transaction.id,
                        "refunded",
                        error_message=error_str
                    )
                
                logger.info(f"[PAYMENT] Refunded {star_cost} stars to user {user.telegram_id}")
                
                # Try to send error message
                try:
                    await message.answer(
                        f"❌ <b>Произошла ошибка при выполнении охоты</b>\n\n"
                        f"Ваши {star_cost} ⭐ возвращены."
                    )
                except Exception as e3:
                    logger.error(f"[PAYMENT] Failed to send error message: {e3}")
        
        # No need for second commit here
        # await session.commit()
