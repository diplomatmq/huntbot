from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import Inventory, Weapon
from bot.database.queries import get_or_create_user, update_energy, add_coins
from bot.keyboards.inventory_kb import get_inventory_keyboard

router = Router()


def format_item_name(name: str) -> str:
    return name.replace("_", " ").capitalize()


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


def get_sell_keyboard(items):
    buttons = []
    
    # Add "Sell All" button at the top if there are items to sell
    sellable_items = [item for item in items if item.item_type not in ["weapon", "potion"]]
    if sellable_items:
        buttons.append([InlineKeyboardButton(text="💰 Продать всё", callback_data="sell_all_items")])
        buttons.append([InlineKeyboardButton(text="➖➖➖➖➖", callback_data="separator")])
    
    for item in sellable_items:
        buttons.append([
            InlineKeyboardButton(
                text=f"Продать {format_item_name(item.item_name)} (x{item.quantity})",
                callback_data=f"sell_item_{item.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="inventory")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_equip_keyboard(weapons):
    buttons = []
    for weapon in weapons:
        status = " (экипирован)" if weapon.is_equipped else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{weapon.weapon_type.capitalize()}{status}",
                callback_data=f"equip_weapon_{weapon.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="inventory")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "inventory")
async def show_inventory(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)
        weapons = await get_user_weapons(session, user.id)
        inventory_items = await get_user_inventory_items(session, user.id)

        text = "🎒 <b>Инвентарь</b>\n\n"

        # Show weapons
        if weapons:
            text += "🔫 <b>Оружие</b>\n"
            for weapon in weapons:
                status = " (экипирован)" if weapon.is_equipped else ""
                text += f"  {weapon.weapon_type.capitalize()}{status}\n"
            text += "\n"

        # Show other items
        if inventory_items:
            items_by_type = {}
            for item in inventory_items:
                if item.item_type not in items_by_type:
                    items_by_type[item.item_type] = []
                items_by_type[item.item_type].append(item)

            for item_type, items in items_by_type.items():
                type_emoji = {"meat": "🍖", "skin": "🦌", "material": "📦", "bait": "🍖", "ammo": "💨", "potion": "🧪"}.get(item_type, "📦")
                text += f"{type_emoji} <b>{item_type.capitalize()}</b>\n"

                for item in items:
                    rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.rarity, "⚪")
                    text += f"  {rarity_emoji} {format_item_name(item.item_name)} x{item.quantity}\n"

                text += "\n"
        elif not weapons:
            text += "Инвентарь пуст! Посетите магазин!"

    try:
        await callback.message.edit_text(text, reply_markup=get_inventory_keyboard())
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data == "sell_items")
async def sell_items_menu(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        inventory_items = await get_user_inventory_items(session, user.id)

        if not inventory_items:
            text = "💰 <b>Продажа</b>\n\n"
            text += "У вас нет предметов для продажи!"
            await callback.message.edit_text(text, reply_markup=get_inventory_keyboard())
            await callback.answer()
            return

        text = "💰 <b>Продажа предметов</b>\n\n"
        text += "Выберите предмет для продажи:\n"
        await callback.message.edit_text(text, reply_markup=get_sell_keyboard(inventory_items))
        await callback.answer()


@router.callback_query(F.data.startswith("sell_item_"))
async def sell_item(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        
        # Find the item
        result = await session.execute(select(Inventory).where(Inventory.id == item_id, Inventory.user_id == user.id))
        item = result.scalar_one_or_none()
        
        if not item:
            await callback.answer("❌ Предмет не найден!", show_alert=True)
            return
        
        # Calculate price (simple formula: rarity * quantity * 5)
        rarity_multiplier = {
            "common": 1,
            "uncommon": 2,
            "rare": 5,
            "epic": 10,
            "legendary": 25
        }
        price = rarity_multiplier.get(item.rarity, 1) * item.quantity * 5
        
        # Add coins and delete item
        user = await add_coins(session, user, price)
        await session.delete(item)
        await session.commit()
        
        await callback.answer(f"✅ Продано {format_item_name(item.item_name)} за {price} монет!", show_alert=True)
        
        # Refresh inventory view
        await show_inventory(callback)


@router.callback_query(F.data == "sell_all_items")
async def sell_all_items(callback: CallbackQuery):
    """Sell all sellable items at once"""
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        inventory_items = await get_user_inventory_items(session, user.id)
        
        # Filter sellable items (exclude weapons and potions)
        sellable_items = [item for item in inventory_items if item.item_type not in ["weapon", "potion"]]
        
        if not sellable_items:
            await callback.answer("❌ Нет предметов для продажи!", show_alert=True)
            return
        
        # Calculate total price
        rarity_multiplier = {
            "common": 1,
            "uncommon": 2,
            "rare": 5,
            "epic": 10,
            "legendary": 25
        }
        
        total_price = 0
        items_sold = []
        
        for item in sellable_items:
            price = rarity_multiplier.get(item.rarity, 1) * item.quantity * 5
            total_price += price
            items_sold.append(f"{format_item_name(item.item_name)} x{item.quantity}")
            await session.delete(item)
        
        # Add coins
        user = await add_coins(session, user, total_price)
        await session.commit()
        
        # Build message
        items_text = "\n".join([f"• {item}" for item in items_sold[:10]])  # Show max 10 items
        if len(items_sold) > 10:
            items_text += f"\n... и еще {len(items_sold) - 10} предметов"
        
        await callback.answer(
            f"✅ Продано {len(items_sold)} предметов за {total_price} монет!",
            show_alert=True
        )
        
        # Refresh inventory view
        await show_inventory(callback)


@router.callback_query(F.data == "equip")
async def equip_menu(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        weapons = await get_user_weapons(session, user.id)

        if not weapons:
            await callback.answer("❌ У вас нет оружия для экипировки!", show_alert=True)
            return

        text = "🔧 <b>Экипировка</b>\n\n"
        text += "Выберите оружие для экипировки:"
        await callback.message.edit_text(text, reply_markup=get_equip_keyboard(weapons))
        await callback.answer()


@router.callback_query(F.data.startswith("equip_weapon_"))
async def equip_weapon(callback: CallbackQuery):
    weapon_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        weapons = await get_user_weapons(session, user.id)

        # Unequip all weapons first
        for weapon in weapons:
            weapon.is_equipped = False

        # Equip selected one
        result = await session.execute(select(Weapon).where(Weapon.id == weapon_id, Weapon.user_id == user.id))
        selected_weapon = result.scalar_one_or_none()
        
        if not selected_weapon:
            await callback.answer("❌ Оружие не найдено!", show_alert=True)
            return
        
        selected_weapon.is_equipped = True
        await session.commit()
        
        await callback.answer(f"✅ Экипировано {selected_weapon.weapon_type.capitalize()}!", show_alert=True)
        
        # Refresh inventory view
        await show_inventory(callback)
