from aiogram import Router, F
from aiogram.types import Message
from bot.config import ADMIN_IDS

router = Router()


@router.message(F.text == "/admin")
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    text = (
        "🔧 <b>Панель администратора</b>\n\n"
        "Доступные команды:\n"
        "• <code>/stats</code> — Статистика бота\n"
        "• <code>/broadcast [текст]</code> — Рассылка всем игрокам\n"
        "• <code>/addcoins [id] [сумма]</code> — Добавить монеты игроку\n"
        "• <code>/addstars [id] [сумма]</code> — Добавить звёзды игроку"
    )
    await message.answer(text)
