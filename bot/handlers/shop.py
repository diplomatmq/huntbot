from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from bot.database.db import async_session
from bot.database.models import Weapon
from bot.database.queries import get_or_create_user, update_energy, add_coins, consume_inventory_item, add_inventory_item
from bot.keyboards.shop_kb import get_shop_keyboard, get_shop_category_keyboard, get_payment_keyboard

router = Router()


def _is_shop_main_callback(data: str) -> bool:
    parts = data.split("_")
    return len(parts) == 2 and parts[0] == "shop" and parts[1].isdigit()


@router.callback_query(F.data.func(_is_shop_main_callback))
async def show_shop(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)

        text = (
            f"🛒 <b>Магазин</b>\n\n"
            f"💰 Ваши монеты: {user.coins}\n"
            f"⭐ Ваши звёзды: {user.stars}\n\n"
            f"Выберите категорию:"
        )

        try:
            await callback.message.edit_text(text, reply_markup=get_shop_keyboard(callback.from_user.id))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("shop_category_"))
async def show_shop_category(callback: CallbackQuery):
    category = callback.data.split("_")[2]  # shop_category_weapons_userId

    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)

        shop_items = {
            "weapons": [
                {"name": "Лук", "price": 500, "currency": "coins", "type": "bow"},
                {"name": "Арбалет", "price": 2500, "currency": "coins", "type": "crossbow"},
                {"name": "Винтовка", "price": 15000, "currency": "coins", "type": "rifle"},
                {"name": "Дробовик", "price": 10000, "currency": "coins", "type": "shotgun"},
            ],
            "ammo": [
                {"name": "Стрелы (10шт)", "price": 50, "currency": "coins", "type": "arrows"},
                {"name": "Патроны (10шт)", "price": 100, "currency": "coins", "type": "bullets"},
            ],
            "bait": [
                {"name": "Приманка травоядная", "price": 25, "currency": "coins", "type": "bait_herbivore"},
                {"name": "Приманка хищная", "price": 35, "currency": "coins", "type": "bait_predator"},
            ],
            "potions": [
                {"name": "Зелье энергии", "price": 100, "currency": "coins", "type": "potion_energy"},
                {"name": "Зелье удачи", "price": 5, "currency": "stars", "type": "potion_luck"},
            ]
        }

        items = shop_items.get(category, [])

        category_names = {
            "weapons": "🔫 Оружие",
            "ammo": "💨 Боеприпасы",
            "bait": "🍖 Приманки",
            "potions": "🧪 Зелья"
        }

        text = f"{category_names.get(category, '🛒 Магазин')}\n\n"

        for item in items:
            currency = "💰" if item["currency"] == "coins" else "⭐"
            text += f"• {item['name']} — {currency} {item['price']}\n"

        try:
            await callback.message.edit_text(text, reply_markup=get_shop_category_keyboard(callback.from_user.id, category, items))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: CallbackQuery):
    from bot.utils.telegram_api import TelegramBotAPI
    from bot.config import BOT_TOKEN
    from bot.database.queries import create_stars_transaction
    from datetime import datetime
    
    item_data = callback.data.split("_", 1)[1]
    parts = item_data.split("_")
    item_name = "_".join(parts[:-3]).replace("_", " ")
    price = int(parts[-3])
    currency = parts[-2]
    # Last part is user_id, ignored here as middleware already checked it
    
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        
        if currency == "stars":
            # Create payment link for stars
            telegram_api = TelegramBotAPI(BOT_TOKEN)
            timestamp = int(datetime.now().timestamp())
            payload = f"shop_{item_name.replace(' ', '_')}_{callback.from_user.id}_{timestamp}"
            invoice_link = await telegram_api.create_invoice_link(
                title=item_name.capitalize(),
                description=f"Покупка: {item_name.capitalize()}",
                payload=payload,
                currency="XTR",
                prices=[{"label": item_name.capitalize(), "amount": price}],
                provider_token=None
            )
            
            # Save transaction
            await create_stars_transaction(
                session,
                user.id,
                payload,
                invoice_link,
                price,
                message_id=callback.message.message_id,
                chat_id=callback.message.chat.id
            )
            
            await callback.message.answer(
                f"💳 <b>Оплата товара</b>\n\n"
                f"🧪 {item_name.capitalize()}\n"
                f"💰 Цена: {price} ⭐\n\n"
                f"Нажмите на ссылку для оплаты:",
                reply_markup=get_payment_keyboard(callback.from_user.id, invoice_link)
            )
            await callback.answer("✅ Ссылка на оплату отправлена!")
            return
        
        if currency == "coins":
            if user.coins < price:
                await callback.answer("❌ Недостаточно монет!", show_alert=True)
                return
            user.coins -= price
        
        # Add item to inventory or weapons
        is_weapon = any(w in item_name.lower() for w in ["лук", "арбалет", "винтовка", "дробовик"])
        if is_weapon:
            # Determine weapon type
            weapon_types = {
                "лук": "bow",
                "арбалет": "crossbow",
                "винтовка": "rifle",
                "дробовик": "shotgun"
            }
            weapon_type = None
            for name, wtype in weapon_types.items():
                if name in item_name.lower():
                    weapon_type = wtype
                    break
            
            if weapon_type:
                new_weapon = Weapon(
                    user_id=user.id,
                    weapon_type=weapon_type,
                    level=1,
                    durability=100,
                    max_durability=100,
                    is_equipped=False
                )
                session.add(new_weapon)
        else:
            # Add to inventory
            item_type = "material"
            if "приманка" in item_name.lower():
                item_type = "bait"
            elif "стрелы" in item_name.lower() or "патроны" in item_name.lower():
                item_type = "ammo"
            elif "зелье" in item_name.lower():
                item_type = "potion"
            
            await add_inventory_item(session, user.id, item_name, item_type, 1, "common")
        
        await session.commit()
    
    await callback.answer(f"✅ Куплено: {item_name.capitalize()}!")
    
    # Refresh shop
    await show_shop(callback)


# Payment handlers for potions
from sqlalchemy import select, and_
from bot.database.models import StarsTransaction
from bot.database.queries import update_stars_transaction
from datetime import datetime

# Protection against duplicate payments
paid_shop_payloads = set()
PAID_SHOP_PAYLOADS_MAX = 1000


@router.pre_checkout_query(F.invoice_payload.startswith("shop_"))
async def process_pre_checkout_query_shop(pre_checkout_query: PreCheckoutQuery):
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

        # Check if transaction belongs to this user (compare by database user.id)
        if transaction.user_id != user.id:
            await pre_checkout_query.answer(ok=False, error_message="Этот инвойс создан для другого пользователя.")
            return

        # Check if already paid
        if payload in paid_shop_payloads:
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


async def handle_shop_payment(message: Message, payload: str, telegram_payment_id: str):
    """Handle successful shop payment (called from hunt.py)"""
    global paid_shop_payloads
    successful_payment = message.successful_payment
    star_cost = successful_payment.total_amount

    # Protection against duplicate payments
    if payload in paid_shop_payloads:
        return

    # Mark payload as paid
    if len(paid_shop_payloads) >= PAID_SHOP_PAYLOADS_MAX:
        old_entries = list(paid_shop_payloads)
        paid_shop_payloads = set(old_entries[len(old_entries)//2:])
    paid_shop_payloads.add(payload)

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

        # Extract item name from payload: shop_{item_name}_{user_id}_{timestamp}
        parts = payload.split("_")
        item_name = "_".join(parts[1:-2]).replace("_", " ")

        # Add item to inventory
        item_type = "potion"
        if "приманка" in item_name.lower():
            item_type = "bait"
        elif "стрелы" in item_name.lower() or "патроны" in item_name.lower():
            item_type = "ammo"

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[SHOP_PAYMENT] Adding item: name='{item_name}', type='{item_type}'")

        await add_inventory_item(session, user.id, item_name, item_type, 1, "common")
        await session.commit()

        await message.answer(
            f"✅ <b>Оплата успешна!</b>\n\n"
            f"🧪 Получено: {item_name.capitalize()}\n"
            f"Товар добавлен в ваш инвентарь.",
            reply_to_message_id=reply_to_id
        )
