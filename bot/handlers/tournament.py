from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from bot.config import ADMIN_IDS
from bot.database.db import async_session
from bot.database.models import Tournament
from bot.database.queries import (
    get_all_users,
    get_current_tournament,
    get_tournament_top,
)
from bot.states.tournament import TournamentStates

router = Router()
DATE_FORMAT = "%Y-%m-%d %H:%M"
METRIC_LABELS = {"weight": "общий вес", "animals": "количество животных"}


def _is_private_admin(message: Message) -> bool:
    return message.chat.type == "private" and message.from_user.id in ADMIN_IDS


def _confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Создать", callback_data="tour_confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="tour_cancel"),
        ]
    ])


def _metric_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Общий вес (кг)", callback_data="tour_metric_weight")],
        [InlineKeyboardButton(text="🦌 Количество животных", callback_data="tour_metric_animals")],
    ])


def _parse_date(value: str):
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT)
    except ValueError:
        return None


@router.message(Command("new_tour"))
async def cmd_new_tour(message: Message, state: FSMContext):
    if not _is_private_admin(message):
        return
    await state.clear()
    await state.set_state(TournamentStates.name)
    await message.answer("Введите название турнира:")


@router.message(TournamentStates.name)
async def tournament_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Введите название турнира:")
        return
    await state.update_data(name=name)
    await state.set_state(TournamentStates.starts_at)
    await message.answer("Введите дату начала в UTC в формате YYYY-MM-DD HH:MM:")


@router.message(TournamentStates.starts_at)
async def tournament_starts_at(message: Message, state: FSMContext):
    starts_at = _parse_date(message.text or "")
    if starts_at is None:
        await message.answer("Неверный формат. Используйте YYYY-MM-DD HH:MM, например 2026-10-01 12:00:")
        return
    await state.update_data(starts_at=starts_at.isoformat())
    await state.set_state(TournamentStates.ends_at)
    await message.answer("Введите дату окончания в UTC в формате YYYY-MM-DD HH:MM:")


@router.message(TournamentStates.ends_at)
async def tournament_ends_at(message: Message, state: FSMContext):
    ends_at = _parse_date(message.text or "")
    data = await state.get_data()
    starts_at = datetime.fromisoformat(data["starts_at"])
    if ends_at is None or ends_at <= starts_at:
        await message.answer("Дата окончания должна быть позже начала. Повторите ввод в формате YYYY-MM-DD HH:MM:")
        return
    await state.update_data(ends_at=ends_at.isoformat())
    await state.set_state(TournamentStates.winners_count)
    await message.answer("Сколько будет победителей? Введите целое число:")


@router.message(TournamentStates.winners_count)
async def tournament_winners_count(message: Message, state: FSMContext):
    try:
        winners_count = int((message.text or "").strip())
    except ValueError:
        winners_count = 0
    if winners_count < 1:
        await message.answer("Введите положительное целое число победителей:")
        return
    await state.update_data(winners_count=winners_count)
    await state.set_state(TournamentStates.metric)
    await message.answer("Выберите, что считать в турнире:", reply_markup=_metric_keyboard())


@router.callback_query(TournamentStates.metric, F.data.startswith("tour_metric_"))
async def tournament_metric(callback: CallbackQuery, state: FSMContext):
    metric = callback.data.removeprefix("tour_metric_")
    await state.update_data(metric=metric)
    await state.set_state(TournamentStates.confirmation)
    data = await state.get_data()
    starts_at = datetime.fromisoformat(data["starts_at"])
    ends_at = datetime.fromisoformat(data["ends_at"])
    await callback.message.edit_text(
        f"Проверьте турнир:\n\n"
        f"🏆 {data['name']}\n"
        f"📊 Тип: {METRIC_LABELS[metric]}\n"
        f"🕐 Начало UTC: {starts_at:%Y-%m-%d %H:%M}\n"
        f"🕐 Конец UTC: {ends_at:%Y-%m-%d %H:%M}\n"
        f"🥇 Победителей: {data['winners_count']}\n\n"
        "Создать турнир?",
        reply_markup=_confirmation_keyboard(),
    )
    await callback.answer()


@router.callback_query(TournamentStates.confirmation, F.data == "tour_cancel")
async def cancel_tournament(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Создание турнира отменено.")
    await callback.answer()


@router.callback_query(TournamentStates.confirmation, F.data == "tour_confirm")
async def confirm_tournament(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    starts_at = datetime.fromisoformat(data["starts_at"])
    ends_at = datetime.fromisoformat(data["ends_at"])
    async with async_session() as session:
        tournament = Tournament(
            name=data["name"],
            metric=data["metric"],
            starts_at=starts_at,
            ends_at=ends_at,
            winners_count=data["winners_count"],
            status="active",
        )
        session.add(tournament)
        await session.commit()
        users = await get_all_users(session)

    announcement = (
        f"🏆 <b>Начался новый турнир!</b>\n\n"
        f"<b>{data['name']}</b>\n"
        f"📊 Считаем: {METRIC_LABELS[data['metric']]}\n"
        f"🕐 Начало UTC: {starts_at:%Y-%m-%d %H:%M}\n"
        f"🕐 Конец UTC: {ends_at:%Y-%m-%d %H:%M}\n"
        f"🥇 Победителей: {data['winners_count']}\n\n"
        "Проверить рейтинг: /tour"
    )
    sent_count = 0
    for user in users:
        try:
            await callback.bot.send_message(user.telegram_id, announcement)
            sent_count += 1
        except Exception:
            continue

    if callback.from_user.id not in {user.telegram_id for user in users}:
        await callback.bot.send_message(callback.from_user.id, announcement)
        sent_count += 1

    await state.clear()
    await callback.message.edit_text(f"Турнир создан. Уведомления отправлены: {sent_count}.")
    await callback.answer()


@router.message(Command("tour"))
async def cmd_tour(message: Message):
    async with async_session() as session:
        tournament = await get_current_tournament(session)
        if tournament is None:
            await message.answer("Сейчас активных турниров нет.")
            return
        rows = await get_tournament_top(session, tournament, limit=10)

    metric = tournament.metric
    lines = []
    for position, (score, user) in enumerate(rows, 1):
        player_name = f"@{user.username}" if user.username else str(user.telegram_id)
        value = f"{score.total_weight:.1f} кг" if metric == "weight" else f"{score.animals_count} животных"
        lines.append(f"{position}. {player_name} — {value}")

    top_text = "\n".join(lines) if lines else "Пока никто не набрал результат."
    await message.answer(
        f"🏆 <b>{tournament.name}</b>\n"
        f"📊 {METRIC_LABELS[metric]}\n"
        f"🕐 До {tournament.ends_at:%Y-%m-%d %H:%M} UTC\n"
        f"🥇 Победителей: {tournament.winners_count}\n\n"
        f"<b>Топ-10:</b>\n{top_text}"
    )
