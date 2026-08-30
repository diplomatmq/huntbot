from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


QUESTS_PER_PAGE = 5


def _nav_buttons(user_id: int, section: str, page: int, total_pages: int) -> list:
    nav = []
    if total_pages > 1:
        if page > 1:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"questpage_{section}_{page - 1}_{user_id}"))
        nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=f"questinfo_none_{user_id}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"questpage_{section}_{page + 1}_{user_id}"))
    return nav


def get_quests_overview_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 Активные", callback_data=f"questlist_active_1_{user_id}"),
            InlineKeyboardButton(text="📋 Доступные", callback_data=f"questlist_available_1_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"quests_{user_id}"),
            InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}")
        ]
    ])


def get_quest_list_keyboard(user_id: int, section: str, quests_display: list[tuple[int, str]],
                            page: int, total_pages: int, back_to_overview=True):
    buttons = []
    for qid, label in quests_display:
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"questdetail_{qid}_{section}_{page}_{user_id}")])

    nav = _nav_buttons(user_id, section, page, total_pages)
    if nav:
        buttons.append(nav)

    footer = []
    if back_to_overview:
        footer.append(InlineKeyboardButton(text="🔙 Назад", callback_data=f"quests_{user_id}"))
    footer.append(InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}"))
    buttons.append(footer)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quest_detail_keyboard(user_id: int, quest_id: int, is_taken: bool, is_active: bool,
                              section: str, return_page: int, can_take=True, is_repeatable=False):
    buttons = []
    if not is_taken and can_take:
        buttons.append([InlineKeyboardButton(text="✅ Взять квест", callback_data=f"take_quest_{quest_id}_{user_id}")])
    elif is_active:
        buttons.append([InlineKeyboardButton(text="🔥 В работе", callback_data=f"questinfo_none_{user_id}")])
    elif is_taken and is_repeatable:
        buttons.append([InlineKeyboardButton(text="🔄 Взять снова", callback_data=f"take_quest_{quest_id}_{user_id}")])
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад к списку", callback_data=f"questlist_{section}_{return_page}_{user_id}"),
        InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
