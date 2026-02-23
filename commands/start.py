"""
КОМАНДА /start
Информация о боте
"""
from telegram.ext import CommandHandler
from permissions import is_admin, is_owner
from config import OWNER_ID
from database import get_all_chats, get_all_admins, get_all_moderators_db
from constants import RANKS

async def cmd_start(update, context):
    """Информация о боте"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    # Статус пользователя
    if is_owner(user_id):
        status = "👑 Владелец"
    else:
        status = "🛡️ Администратор"
    
    # Статистика
    chats = get_all_chats()
    admins = get_all_admins()
    moders = get_all_moderators_db()
    
    # Получаем ранг
    from database import get_user_rank_db
    rank = get_user_rank_db(user_id)
    rank_name = RANKS.get(rank, {}).get('name', 'Участник')
    
    await update.message.reply_text(
        f"✅ <b>Бот работает!</b>\n\n"
        f"👤 <b>Ваш статус:</b> {status}\n"
        f"🎖️ <b>Ваш ранг:</b> {rank_name}\n"
        f"🆔 <b>Ваш ID:</b> <code>{user_id}</code>\n"
        f"👑 <b>Владелец:</b> <code>{OWNER_ID}</code>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Чатов: {len(chats)}\n"
        f"• Админов: {len(admins)}\n"
        f"• Модераторов: {len(moders)}\n\n"
        f"📝 Используйте /help для списка команд",
        parse_mode='HTML'
    )

def register(app):
    app.add_handler(CommandHandler("start", cmd_start))