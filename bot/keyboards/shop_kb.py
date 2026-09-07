from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_shop_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="🔫 Оружие", callback_data=f"shop_category_weapons_{user_id}"),
            InlineKeyboardButton(text="💨 Боеприпасы", callback_data=f"shop_category_ammo_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🍖 Приманки", callback_data=f"shop_category_bait_{user_id}"),
            InlineKeyboardButton(text="🧪 Зелья", callback_data=f"shop_category_potions_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_shop_category_keyboard(user_id: int, category: str, items: list, user=None):
    buttons = []
    
    for item in items:
        item_id = item["name"].lower().replace(" ", "_")
        callback_data = f"buy_{item_id}_{item['price']}_{item['currency']}_{user_id}"
        buttons.append([
            InlineKeyboardButton(
                text=f"{item['name']} — {item['price']} {item['currency']}",
                callback_data=callback_data
            )
        ])
    
    # Add bulk purchase buttons for bait and potions (except luck potions)
    if category in ["bait", "potions"]:
        bulk_buttons = []
        for item in items:
            # Skip luck potion for bulk purchase
            if item["type"] == "potion_luck":
                continue
            
            item_id = item["name"].lower().replace(" ", "_")
            bulk_callback_data = f"bulk_{item_id}_{item['price']}_{item['currency']}_{user_id}"
            bulk_buttons.append(
                InlineKeyboardButton(
                    text=f"📦 {item['name']} (оптом)",
                    callback_data=bulk_callback_data
                )
            )
        
        if bulk_buttons:
            buttons.append(bulk_buttons)
    
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"shop_{user_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_keyboard(user_id: int, invoice_link: str):
    """Keyboard with payment link"""
    buttons = [
        [InlineKeyboardButton(text="💳 Оплатить", url=invoice_link)],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data=f"shop_{user_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
