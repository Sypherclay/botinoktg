"""
ОЧИСТКА ЧАТА
!cleanchat
"""
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
from permissions import is_owner
from database import (
    delete_user_warnings, delete_user_stats,
    delete_user_from_all_topics, delete_user_salary,
    delete_user_complaints_data, delete_user_rewards,
    delete_user_vacation, delete_user_auto_warn_count,
    delete_user_milestones, delete_user_rank,
    get_all_users_in_chat
)

async def cmd_cleanchat(update, context):
    """Очистка проблемных данных текущего чата"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ Только владелец")
        return
    
    chat_id = str(update.effective_chat.id)
    
    msg = await update.message.reply_text("🧹 Очистка данных...")
    
    cleaned = 0
    users = get_all_users_in_chat(chat_id)
    
    for uid, name, username in users:
        if uid in [777000, 1087968824]:
            delete_user_warnings(uid, chat_id)
            delete_user_from_all_topics(uid, chat_id)
            delete_user_stats(uid, chat_id)
            delete_user_salary(uid)
            delete_user_complaints_data(uid)
            delete_user_rewards(uid)
            delete_user_vacation(uid)
            delete_user_auto_warn_count(uid)
            delete_user_milestones(uid, chat_id)
            delete_user_rank(uid)
            cleaned += 1
    
    await msg.edit_text(
        f"✅ <b>Очистка завершена!</b>\n\n"
        f"🧹 Удалено проблемных записей: {cleaned}\n"
        f"👥 Всего пользователей: {len(users)}",
        parse_mode=ParseMode.HTML
    )

def register(app):
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!cleanchat\b'), cmd_cleanchat))