import math
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from bot.database.db import async_session
from bot.database.queries import get_or_create_user, update_energy, get_active_quests, get_available_quests
from bot.keyboards.quest_kb import (
    get_quests_overview_keyboard,
    get_quest_list_keyboard,
    get_quest_detail_keyboard,
    QUESTS_PER_PAGE,
)
from bot.game_logic.locations import get_unlocked_locations, get_location
from bot.database.models import Quest, UserQuest
from sqlalchemy import select

router = Router()


QUEST_TYPE_LABEL = {"main": "📖 Сюжет", "side": "📋 Побоч"}


def _format_condition(conditions: dict, progress: dict | None) -> str:
    progress = progress or {}
    lines = []
    if conditions.get("kill"):
        c = conditions["kill"]
        cur = progress.get("killed", 0)
        lines.append(f"🎯 Убить животных: «{c['animal']}» — {cur}/{c['count']}")
    if conditions.get("collect"):
        c = conditions["collect"]
        cur = progress.get("collected", 0)
        lines.append(f"🎒 Собрать: «{c['item']}» — {cur}/{c['count']}")
    if conditions.get("explore"):
        c = conditions["explore"]
        cur = progress.get("explored", 0)
        loc = get_location(c["location"])
        loc_label = f"{loc.emoji} {loc.name}" if loc else c["location"]
        lines.append(f"🗺️ Исследовать: {loc_label} — {cur}/{c['count']}")
    return "\n".join(lines) if lines else "—"


def _label_for_quest(q: Quest, uq: UserQuest | None) -> str:
    prefix = QUEST_TYPE_LABEL.get(q.quest_type, "📋")
    progress_part = ""
    status_icon = ""
    if uq:
        if uq.status == "active":
            status_icon = "🔥 "
        elif uq.status == "completed":
            status_icon = "✅ "
        if q.conditions.get("kill"):
            need = q.conditions["kill"]["count"]
            cur = uq.progress.get("killed", 0) if uq.progress else 0
            progress_part = f" [{cur}/{need}]"
        elif q.conditions.get("collect"):
            need = q.conditions["collect"]["count"]
            cur = uq.progress.get("collected", 0) if uq.progress else 0
            progress_part = f" [{cur}/{need}]"
    loc = get_location(q.location)
    loc_emoji = loc.emoji if loc else ""
    label = f"{status_icon}{prefix} {loc_emoji} {q.title}{progress_part}"
    if len(label) > 60:
        label = label[:57] + "..."
    return label


def _build_reward_text(q: Quest) -> str:
    parts = []
    if q.reward_exp:
        parts.append(f"+{q.reward_exp} опыта")
    if q.reward_coins:
        parts.append(f"+{q.reward_coins} монет")
    if q.reward_stars:
        parts.append(f"+{q.reward_stars} звёзд")
    if q.progress_reward:
        parts.append(f"+{q.progress_reward}% прогресса локации")
    if q.reward_items:
        for ri in q.reward_items:
            parts.append(f"+{ri.get('quantity',1)}× {ri.get('item','?')}")
    return ", ".join(parts) if parts else "—"


async def _collect_all_quest_display(session, user):
    active_uqs = await get_active_quests(session, user.id)
    active_pairs = [
        (uq.quest.id, _label_for_quest(uq.quest, uq), "active", uq)
        for uq in active_uqs
    ]

    unlocked_locs = get_unlocked_locations(user.location_progress, "story")
    unlocked_ids = [loc.id for loc in unlocked_locs]
    available_quests = await get_available_quests(
        session, user.level, user.id, location_ids=unlocked_ids
    )
    available_pairs = [
        (q.id, _label_for_quest(q, None), "available", None)
        for q in available_quests
    ]

    return active_pairs, available_pairs


async def _render_all_quests(callback: CallbackQuery, page: int = 1):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)

        if user.game_mode != "story":
            await callback.answer("❌ Квесты доступны только в сюжетном режиме!", show_alert=True)
            return

        active_pairs, available_pairs = await _collect_all_quest_display(session, user)

    combined = []
    for qid, label, section, uq in active_pairs:
        combined.append((qid, label, "active", uq))
    for qid, label, section, uq in available_pairs:
        combined.append((qid, label, "available", uq))

    total_count = len(combined)
    total_pages = max(1, math.ceil(total_count / QUESTS_PER_PAGE))
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    start = (page - 1) * QUESTS_PER_PAGE
    page_slice = combined[start:start + QUESTS_PER_PAGE]

    active_count = len(active_pairs)
    available_count = len(available_pairs)

    header = (
        f"📜 <b>Квесты</b> (Сюжетный режим, стр. {page}/{total_pages})\n\n"
        f"🔥 Активных: <b>{active_count}</b>   📋 Доступных: <b>{available_count}</b>\n\n"
    )
    if not combined:
        text = header + "Нет квестов. Выполняйте охоту и получайте новые уровни, чтобы открыть больше заданий!"
        display_for_kb = []
    else:
        display_for_kb = [(qid, label) for qid, label, _, _ in page_slice]
        lines = []
        for idx, (qid, label, section, uq) in enumerate(page_slice, start=start + 1):
            lines.append(f"{idx}. {label}")
        text = header + "\n".join(lines)

    kb = get_quest_list_keyboard(
        callback.from_user.id, "all", display_for_kb, page, total_pages,
        back_to_overview=False
    )
    rows = list(kb.inline_keyboard)
    footer_row = []
    if active_count > 0:
        footer_row.append(
            InlineKeyboardButton(text=f"🔥 Активные ({active_count})", callback_data=f"questlist_active_1_{callback.from_user.id}")
        )
    if available_count > 0:
        footer_row.append(
            InlineKeyboardButton(text=f"📋 Доступные ({available_count})", callback_data=f"questlist_available_1_{callback.from_user.id}")
        )
    if footer_row:
        rows.insert(-1, footer_row)
    from aiogram.types import InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except (TelegramBadRequest, TelegramRetryAfter) as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


async def _render_overview(callback: CallbackQuery):
    await _render_all_quests(callback, page=1)


@router.callback_query(F.data.startswith("quests_"))
async def show_quests(callback: CallbackQuery):
    parts = callback.data.split("_")
    try_page = 1
    if len(parts) >= 3 and parts[1].isdigit():
        try:
            try_page = int(parts[1])
        except ValueError:
            pass
    await _render_all_quests(callback, page=try_page)


async def _collect_active_display_pairs(session, user_id):
    uqs = await get_active_quests(session, user_id)
    return [(uq.quest.id, _label_for_quest(uq.quest, uq)) for uq in uqs], uqs


async def _collect_available_display_pairs(session, user):
    unlocked_locs = get_unlocked_locations(user.location_progress, "story")
    unlocked_ids = [loc.id for loc in unlocked_locs]
    quests = await get_available_quests(session, user.level, user.id, location_ids=unlocked_ids)
    return [(q.id, _label_for_quest(q, None)) for q in quests], quests


@router.callback_query(F.data.regexp(r"^questlist_(active|available|all)_\d+_\d+$"))
async def show_quest_list(callback: CallbackQuery):
    parts = callback.data.split("_")
    section = parts[1]
    try:
        page = int(parts[2])
    except ValueError:
        page = 1

    if section == "all":
        await _render_all_quests(callback, page=page)
        return

    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)

        if user.game_mode != "story":
            await callback.answer("❌ Квесты только в сюжетном режиме!", show_alert=True)
            return

        if section == "active":
            display, uqs = await _collect_active_display_pairs(session, user.id)
            section_title = "🔥 Активные квесты"
            if not display:
                text = (
                    f"📜 <b>{section_title}</b>\n\n"
                    f"Нет активных квестов. Перейдите в раздел «📋 Доступные» и возьмите задание."
                )
                kb = get_quest_list_keyboard(callback.from_user.id, section, [], 1, 1)
                try:
                    await callback.message.edit_text(text, reply_markup=kb)
                except (TelegramBadRequest, TelegramRetryAfter) as e:
                    if "message is not modified" not in str(e):
                        raise
                await callback.answer()
                return
        else:
            display, quests = await _collect_available_display_pairs(session, user)
            section_title = "📋 Доступные квесты"
            if not display:
                text = (
                    f"📜 <b>{section_title}</b>\n\n"
                    f"Нет новых квестов. Выполняй активные или повышай уровень / прогресс локаций."
                )
                kb = get_quest_list_keyboard(callback.from_user.id, section, [], 1, 1)
                try:
                    await callback.message.edit_text(text, reply_markup=kb)
                except (TelegramBadRequest, TelegramRetryAfter) as e:
                    if "message is not modified" not in str(e):
                        raise
                await callback.answer()
                return

    total_pages = max(1, math.ceil(len(display) / QUESTS_PER_PAGE))
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    start = (page - 1) * QUESTS_PER_PAGE
    page_slice = display[start:start + QUESTS_PER_PAGE]

    header = f"📜 <b>{section_title}</b> (стр. {page}/{total_pages})\n\n"
    lines = []
    for idx, (qid, label) in enumerate(page_slice, start=start + 1):
        lines.append(f"{idx}. {label}")

    text = header + "\n".join(lines)
    kb = get_quest_list_keyboard(callback.from_user.id, section, page_slice, page, total_pages)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except (TelegramBadRequest, TelegramRetryAfter) as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data.regexp(r"^questpage_(active|available|all)_\d+_\d+$"))
async def quest_paginate(callback: CallbackQuery):
    parts = callback.data.split("_")
    section = parts[1]
    try:
        page = int(parts[2])
    except ValueError:
        page = 1
    callback_data = f"questlist_{section}_{page}_{callback.from_user.id}"
    callback.data = callback_data
    await show_quest_list(callback)


@router.callback_query(F.data.startswith("questdetail_"))
async def quest_detail(callback: CallbackQuery):
    parts = callback.data.split("_")
    # questdetail_{qid}_{section}_{page}_{userId}
    try:
        quest_id = int(parts[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверная ссылка", show_alert=True)
        return
    section = parts[2] if len(parts) > 3 else "active"
    try:
        return_page = int(parts[3]) if len(parts) > 4 else 1
    except ValueError:
        return_page = 1

    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)

        res = await session.execute(select(Quest).where(Quest.id == quest_id))
        quest = res.scalar_one_or_none()
        if not quest:
            await callback.answer("❌ Квест не найден", show_alert=True)
            return

        uq_res = await session.execute(
            select(UserQuest).where(
                UserQuest.user_id == user.id,
                UserQuest.quest_id == quest_id,
            ).order_by(UserQuest.id.desc())
        )
        uq = uq_res.scalars().first()

    loc = get_location(quest.location)
    loc_line = f"{loc.emoji} {loc.name}" if loc else quest.location
    qtype = QUEST_TYPE_LABEL.get(quest.quest_type, "📋")
    repeatable = " 🔁 (повторяемый)" if getattr(quest, "is_repeatable", False) else ""

    if uq and uq.status == "active":
        status = "🔥 В работе"
    elif uq and uq.status == "completed":
        status = "✅ Завершён"
    else:
        status = "📋 Доступен"

    progress = uq.progress if uq else None
    header = (
        f"{qtype} <b>{quest.title}</b>{repeatable}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Локация:</b> {loc_line}\n"
        f"<b>Требуется уровень:</b> {quest.required_level}\n\n"
    )
    description = f"<i>{quest.description}</i>\n\n"
    condition = f"<b>Задание:</b>\n{_format_condition(quest.conditions, progress)}\n\n"
    reward = f"<b>Награда:</b>\n{_build_reward_text(quest)}"

    text = header + description + condition + reward

    can_take = True
    is_taken = uq is not None and uq.status in {"active", "completed"}
    if uq and uq.status == "active":
        can_take = False
    if uq and uq.status == "completed" and not getattr(quest, "is_repeatable", False):
        can_take = False

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_quest_detail_keyboard(
                callback.from_user.id,
                quest_id,
                is_taken=is_taken,
                is_active=(uq is not None and uq.status == "active"),
                section=section,
                return_page=return_page,
                can_take=can_take,
                is_repeatable=getattr(quest, "is_repeatable", False),
            ),
        )
    except (TelegramBadRequest, TelegramRetryAfter) as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data.startswith("questinfo_"))
async def quest_info_stub(callback: CallbackQuery):
    await callback.answer("Страница квестов")


@router.callback_query(F.data.startswith("take_quest_"))
async def take_quest(callback: CallbackQuery):
    # take_quest_{questId}_{userId}
    parts = callback.data.split("_")
    try:
        quest_id = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверная ссылка", show_alert=True)
        return

    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)

        if user.game_mode != "story":
            await callback.answer("❌ Квесты доступны только в сюжетном режиме!", show_alert=True)
            return

        res = await session.execute(select(Quest).where(Quest.id == quest_id))
        quest = res.scalar_one_or_none()
        if not quest:
            await callback.answer("❌ Квест не найден!", show_alert=True)
            return

        # Check if there's already an active quest
        result = await session.execute(
            select(UserQuest).where(
                UserQuest.user_id == user.id,
                UserQuest.quest_id == quest_id,
                UserQuest.status == "active",
            )
        )
        if result.scalar_one_or_none():
            await callback.answer("❌ Квест уже взят!", show_alert=True)
            await _render_overview(callback)
            return

        # For repeatable quests, check if there's a completed one and reset it
        if getattr(quest, "is_repeatable", False):
            completed_result = await session.execute(
                select(UserQuest).where(
                    UserQuest.user_id == user.id,
                    UserQuest.quest_id == quest_id,
                    UserQuest.status == "completed",
                )
            )
            completed_uq = completed_result.scalar_one_or_none()
            if completed_uq:
                # Reset the completed quest to active
                completed_uq.status = "active"
                completed_uq.progress = {}
                await session.commit()
                await callback.answer(f"🔄 Квест «{quest.title}» взят снова!")
                await show_quest_list(callback)
                return

        user_quest = UserQuest(user_id=user.id, quest_id=quest_id, status="active", progress={})
        session.add(user_quest)
        await session.commit()

    await callback.answer(f"✅ Квест «{quest.title}» взят!")
    await show_quest_list(callback)
