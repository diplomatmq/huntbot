from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import Inventory, Weapon
from bot.database.queries import get_or_create_user, update_energy, add_coins
from bot.keyboards.inventory_kb import get_inventory_keyboard
from bot.utils.retry import retry

router = Router()

_sell_wait: dict[int, dict] = {}
_sell_all_wait: set[int] = set()


def format_item_name(name: str) -> str:
    return name


def _item_type_label(t: str) -> str:
    return {
        "meat": "🍖 Мясо",
        "skin": "🦌 Кожа и шкуры",
        "material": "📦 Материалы",
        "bait": "🎁 Приманки",
        "ammo": "💨 Патроны",
        "potion": "🧪 Зелья",
    }.get(t, "📦 Другое")


def _price_per_unit(rarity: str, qty: int) -> int:
    rarity_multiplier = {
        "common": 1,
        "uncommon": 2,
        "rare": 5,
        "epic": 10,
        "legendary": 25,
    }
    return rarity_multiplier.get(rarity, 1) * 5


def _total_price(rarity: str, qty: int) -> int:
    return _price_per_unit(rarity, qty) * qty


async def get_user_inventory_items(session, user_id: int):
    result = await session.execute(
        select(Inventory).where(Inventory.user_id == user_id).order_by(Inventory.item_type, Inventory.item_name)
    )
    return result.scalars().all()


async def get_user_weapons(session, user_id: int):
    result = await session.execute(
        select(Weapon).where(Weapon.user_id == user_id).order_by(Weapon.is_equipped.desc(), Weapon.weapon_type)
    )
    return result.scalars().all()


def get_sell_keyboard(user_id: int, items):
    buttons = []
    sellable_items = [item for item in items if item.item_type not in ["weapon", "potion"]]
    if sellable_items:
        buttons.append([InlineKeyboardButton(text="💰 Продать всё (ввести кол-во)", callback_data=f"sell_all_items_{user_id}")])
        buttons.append([InlineKeyboardButton(text="➖➖➖➖➖", callback_data="separator")])

    for item in sellable_items:
        price_unit = _price_per_unit(item.rarity, 1)
        buttons.append([
            InlineKeyboardButton(
                text=f"Продать {item.item_name} x{item.quantity} ({price_unit}💰/шт)",
                callback_data=f"sell_item_{item.id}_{user_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"inventory_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_equip_keyboard(user_id: int, weapons):
    buttons = []
    for weapon in weapons:
        status = " (экипирован)" if weapon.is_equipped else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{weapon.weapon_type.capitalize()}{status}",
                callback_data=f"equip_weapon_{weapon.id}_{user_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"inventory_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("inventory_"))
@retry(retry_count=3)
async def show_inventory(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)
        weapons = await get_user_weapons(session, user.id)
        inventory_items = await get_user_inventory_items(session, user.id)

        text = "🎒 <b>Инвентарь</b>\n\n"

        if weapons:
            text += "🔫 <b>Оружие</b>\n"
            for weapon in weapons:
                status = " (экипирован)" if weapon.is_equipped else ""
                text += f"  {weapon.weapon_type.capitalize()}{status}\n"
            text += "\n"

        if inventory_items:
            items_by_type = {}
            for item in inventory_items:
                if item.item_type not in items_by_type:
                    items_by_type[item.item_type] = []
                items_by_type[item.item_type].append(item)

            for item_type, items in items_by_type.items():
                text += f"<b>{_item_type_label(item_type)}</b>\n"
                for item in items:
                    rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.rarity, "⚪")
                    text += f"  {rarity_emoji} {item.item_name} x{item.quantity}\n"
                text += "\n"
        elif not weapons:
            text += "Инвентарь пуст! Посетите магазин!"

    try:
        await callback.message.edit_text(text, reply_markup=get_inventory_keyboard(callback.from_user.id))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data.startswith("sell_items_"))
@retry(retry_count=3)
async def sell_items_menu(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        inventory_items = await get_user_inventory_items(session, user.id)

        if not inventory_items:
            text = "💰 <b>Продажа</b>\n\nУ вас нет предметов для продажи!"
            try:
                await callback.message.edit_text(text, reply_markup=get_inventory_keyboard(callback.from_user.id))
            except (TelegramBadRequest, TelegramRetryAfter) as e:
                if "message is not modified" not in str(e):
                    raise
            await callback.answer()
            return

        text = "💰 <b>Продажа предметов</b>\n\n"
        text += "Выберите предмет или Продать всё.\n"
        text += "После выбора напишите в чат <b>число</b> — сколько хотите продать.\n"
        text += "Если Продать всё — напишите 0 = отменить, 1+ = продать все виды."
        try:
            await callback.message.edit_text(text, reply_markup=get_sell_keyboard(callback.from_user.id, inventory_items))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("sell_item_"))
@retry(retry_count=3)
async def sell_item(callback: CallbackQuery):
    parts = callback.data.split("_")
    item_id = int(parts[2])
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        result = await session.execute(select(Inventory).where(Inventory.id == item_id, Inventory.user_id == user.id))
        item = result.scalar_one_or_none()

        if not item:
            await callback.answer("❌ Предмет не найден!", show_alert=True)
            return

        _sell_wait[callback.from_user.id] = {
            "item_id": item.id,
            "name": item.item_name,
            "max_qty": item.quantity,
            "rarity": item.rarity,
            "chat_id": callback.message.chat.id,
            "message_id": callback.message.message_id,
        }
        _sell_all_wait.discard(callback.from_user.id)
        unit = _price_per_unit(item.rarity, 1)
        text = (
            f"💰 <b>Продажа</b>\n\n"
            f"Предмет: <b>{item.item_name}</b>\n"
            f"Количество у вас: <b>{item.quantity}</b>\n"
            f"Цена за 1 штуку: <b>{unit}</b> монет\n"
            f"Продать всё сразу (x{item.quantity}) = <b>{_total_price(item.rarity, item.quantity)}</b> монет\n\n"
            f"👉 Напишите в чат <b>число</b> — сколько хотите продать (от 1 до {item.quantity}).\n"
            f"Отправьте 0, чтобы отменить продажу."
        )
        try:
            await callback.message.edit_text(text)
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
    await callback.answer()


@router.callback_query(F.data.startswith("sell_all_items_"))
@retry(retry_count=3)
async def sell_all_items(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        inventory_items = await get_user_inventory_items(session, user.id)
        sellable_items = [item for item in inventory_items if item.item_type not in ["weapon", "potion"]]

        if not sellable_items:
            await callback.answer("❌ Нет предметов для продажи!", show_alert=True)
            return

        total_max = 0
        preview = []
        for item in sellable_items:
            total_max += _total_price(item.rarity, item.quantity)
            preview.append(f"• {item.item_name} x{item.quantity}")

        _sell_all_wait.add(callback.from_user.id)
        _sell_wait.pop(callback.from_user.id, None)

        preview_text = "\n".join(preview[:8])
        if len(preview) > 8:
            preview_text += f"\n... и ещё {len(preview) - 8} видов"

        text = (
            "💰 <b>Продажа ВСЕХ предметов</b>\n\n"
            f"{preview_text}\n\n"
            f"Общая сумма (если продавать всё): <b>{total_max}</b> монет\n\n"
            f"👉 Напишите в чат <b>1</b> — продать ВСЁ сразу.\n"
            f"👉 Напишите <b>0</b> — отменить."
        )
        try:
            await callback.message.edit_text(text)
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
    await callback.answer()


def _user_in_sell_flow(uid: int) -> bool:
    return uid in _sell_wait or uid in _sell_all_wait


@router.message(F.text.func(lambda text: isinstance(text, str) and text.strip().isdigit() and True))
async def handle_sell_quantity(message: Message):
    uid = message.from_user.id
    if not _user_in_sell_flow(uid):
        return

    text = (message.text or "").strip()
    qty = int(text)

    if uid in _sell_wait:
        spec = _sell_wait.pop(uid)
        if qty <= 0:
            await message.answer("🚫 Продажа отменена.")
            return

        async with async_session() as session:
            user = await get_or_create_user(session, uid, message.from_user.username)
            result = await session.execute(
                select(Inventory).where(Inventory.id == spec["item_id"], Inventory.user_id == user.id)
            )
            item = result.scalar_one_or_none()
            if not item:
                await message.answer("❌ Предмет не найден.")
                return

            if qty > item.quantity:
                qty = item.quantity
                await message.answer(f"⚠️ У вас только {item.quantity} — продаю максимум.")

            total_price = _total_price(item.rarity, qty)
            user = await add_coins(session, user, total_price)

            item.quantity -= qty
            if item.quantity <= 0:
                await session.delete(item)
            await session.commit()

        await message.answer(
            f"✅ Продано {qty}x {spec['name']} за {total_price} монет!",
            reply_to_message_id=message.message_id
        )
        return

    if uid in _sell_all_wait:
        _sell_all_wait.discard(uid)
        if qty <= 0:
            await message.answer("🚫 Продажа всего отменена.")
            return

        async with async_session() as session:
            user = await get_or_create_user(session, uid, message.from_user.username)
            inventory_items = await get_user_inventory_items(session, user.id)
            sellable_items = [item for item in inventory_items if item.item_type not in ["weapon", "potion"]]

            if not sellable_items:
                await message.answer("❌ Нет предметов для продажи!")
                return

            total_price = 0
            count_items = 0
            for item in list(sellable_items):
                price = _total_price(item.rarity, item.quantity)
                total_price += price
                count_items += item.quantity
                await session.delete(item)
            user = await add_coins(session, user, total_price)
            await session.commit()

        await message.answer(
            f"✅ Продано {count_items} предмет(ов/а) за {total_price} монет!",
            reply_to_message_id=message.message_id
        )
        return


@router.callback_query(F.data.startswith("equip_"))
@retry(retry_count=3)
async def equip_menu(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        weapons = await get_user_weapons(session, user.id)

        if not weapons:
            await callback.answer("❌ У вас нет оружия для экипировки!", show_alert=True)
            return

        text = "🔧 <b>Экипировка</b>\n\nВыберите оружие для экипировки:"
        try:
            await callback.message.edit_text(text, reply_markup=get_equip_keyboard(callback.from_user.id, weapons))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("equip_weapon_"))
@retry(retry_count=3)
async def equip_weapon(callback: CallbackQuery):
    import logging
    logger = logging.getLogger(__name__)

    weapon_id = int(callback.data.split("_")[2])
    logger.info(f"[EQUIP] User {callback.from_user.id} trying to equip weapon_id={weapon_id}")

    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        weapons = await get_user_weapons(session, user.id)

        logger.info(f"[EQUIP] User {callback.from_user.id} has {len(weapons)} weapons")

        for weapon in weapons:
            weapon.is_equipped = False

        result = await session.execute(select(Weapon).where(Weapon.id == weapon_id, Weapon.user_id == user.id))
        selected_weapon = result.scalar_one_or_none()

        if not selected_weapon:
            logger.warning(f"[EQUIP] Weapon {weapon_id} not found for user {callback.from_user.id}")
            await callback.answer("❌ Оружие не найдено!", show_alert=True)
            return

        logger.info(f"[EQUIP] Found weapon: {selected_weapon.weapon_type}")
        selected_weapon.is_equipped = True
        await session.commit()

        logger.info(f"[EQUIP] Successfully equipped {selected_weapon.weapon_type}")
        await callback.answer(f"✅ Экипировано {selected_weapon.weapon_type.capitalize()}!", show_alert=True)
        await show_inventory(callback)


def get_potions_keyboard(user_id: int, potions):
    buttons = []
    for potion in potions:
        buttons.append([
            InlineKeyboardButton(
                text=f"{potion.item_name} x{potion.quantity}",
                callback_data=f"use_potion_{potion.id}_{user_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"inventory_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("use_potions_"))
@retry(retry_count=3)
async def use_potions_menu(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        inventory_items = await get_user_inventory_items(session, user.id)
        potions = [item for item in inventory_items if item.item_type == "potion"]

        if not potions:
            text = "🧪 <b>Зелья</b>\n\nУ вас нет зелий! Посетите магазин!"
            try:
                await callback.message.edit_text(text, reply_markup=get_inventory_keyboard(callback.from_user.id))
            except (TelegramBadRequest, TelegramRetryAfter) as e:
                if "message is not modified" not in str(e):
                    raise
            await callback.answer()
            return

        text = "🧪 <b>Зелья</b>\n\nВыберите зелье для использования:"
        try:
            await callback.message.edit_text(text, reply_markup=get_potions_keyboard(callback.from_user.id, potions))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
    await callback.answer()


@router.callback_query(F.data.startswith("use_potion_"))
@retry(retry_count=3)
async def use_potion(callback: CallbackQuery):
    potion_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        result = await session.execute(select(Inventory).where(Inventory.id == potion_id, Inventory.user_id == user.id))
        potion = result.scalar_one_or_none()

        if not potion:
            await callback.answer("❌ Зелье не найдено!", show_alert=True)
            return

        if potion.item_type != "potion":
            await callback.answer("❌ Это не зелье!", show_alert=True)
            return

        # Apply potion effects
        effect_text = ""
        if "энергия" in potion.item_name.lower():
            energy_gain = 20
            user = await update_energy(session, user, energy_gain)
            effect_text = f"⚡ +{energy_gain} энергии"
        elif "удача" in potion.item_name.lower():
            if not user.active_buffs:
                user.active_buffs = {}
            user.active_buffs["luck"] = {"type": "luck", "uses": 5}
            effect_text = "🍀 +5 попыток с повышенной удачей"
        else:
            await callback.answer("❌ Неизвестное зелье!", show_alert=True)
            return

        # Remove potion from inventory
        potion.quantity -= 1
        if potion.quantity <= 0:
            await session.delete(potion)
        await session.commit()

        await callback.answer(f"✅ Использовано {potion.item_name}! {effect_text}", show_alert=True)
        await show_inventory(callback)
