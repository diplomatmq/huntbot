from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_shop_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="🔫 Оружие", callback_data="shop_category_weapons"),
            InlineKeyboardButton(text="💨 Боеприпасы", callback_data="shop_category_ammo")
        ],
        [
            InlineKeyboardButton(text="🍖 Приманки", callback_data="shop_category_bait"),
            InlineKeyboardButton(text="🧪 Зелья", callback_data="shop_category_potions")
        ],
        [
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_shop_category_keyboard(category: str, items: list):
    buttons = []
    
    for item in items:
        item_id = item["name"].lower().replace(" ", "_")
        callback_data = f"buy_{item_id}_{item['price']}_{item['currency']}"
        buttons.append([
            InlineKeyboardButton(
                text=f"{item['name']} — {item['price']} {item['currency']}",
                callback_data=callback_data
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="shop")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_keyboard(invoice_link: str):
    """Keyboard with payment link"""
    buttons = [
        [InlineKeyboardButton(text="💳 Оплатить", url=invoice_link)],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="shop")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
