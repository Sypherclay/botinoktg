"""
УПРАВЛЕНИЕ ЧАТАМИ
Команды: /addchat, /removechat, /listchats
"""
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
from permissions import is_admin
from database import (
    get_all_chats, add_chat_to_db, remove_chat_from_db,
    get_chat_stats, is_moderator_db
)
from logger import log_admin_action, log_command

async def cmd_addchat(update, context):
    """Добавить чат для отслеживания /addchat"""
    user_id = update.effective_user.id
    
    if is_moderator_db(user_id):
        return
    
    if not is_admin(user_id):
        return
    
    if not context.args:
        await update.message.reply_text("Используйте: /addchat ID_чата")
        return
    
    chat_id = context.args[0]
    
    if not chat_id.startswith('-100'):
        await update.message.reply_text("❌ ID должен начинаться с -100")
        return
    
    chats = get_all_chats()
    
    if chat_id not in chats:
        add_chat_to_db(chat_id)
        
        admin_name = update.effective_user.full_name or str(user_id)
        
        log_admin_action(
            admin_id=user_id,
            admin_name=admin_name,
            action="Добавил чат для отслеживания",
            target=chat_id
        )
        
        await update.message.reply_text(f"✅ Чат {chat_id} добавлен")
    else:
        await update.message.reply_text(f"ℹ️ Чат {chat_id} уже есть")

async def cmd_removechat(update, context):
    """Удалить чат из отслеживания /removechat"""
    user_id = update.effective_user.id
    
    if is_moderator_db(user_id):
        return
    
    if not is_admin(user_id):
        return
    
    if not context.args:
        await update.message.reply_text("Используйте: /removechat ID_чата")
        return
    
    chat_id = context.args[0]
    
    chats = get_all_chats()
    
    if chat_id in chats:
        remove_chat_from_db(chat_id)
        
        admin_name = update.effective_user.full_name or str(user_id)
        
        log_admin_action(
            admin_id=user_id,
            admin_name=admin_name,
            action="Удалил чат из отслеживания",
            target=chat_id
        )
        
        await update.message.reply_text(f"✅ Чат {chat_id} удален из отслеживания")
    else:
        await update.message.reply_text(f"❌ Чат {chat_id} не найден в отслеживаемых")

async def cmd_listchats(update, context):
    """Показать список отслеживаемых чатов /listchats"""
    user_id = update.effective_user.id
    
    if is_moderator_db(user_id):
        return
    
    if not is_admin(user_id):
        return
    
    chats = get_all_chats()
    
    if not chats:
        await update.message.reply_text("📭 Чатов нет")
        return
    
    text = "<b>📋 Отслеживаемые чаты:</b>\n\n"
    for chat_id in chats:
        stats = get_chat_stats(chat_id)
        text += f"💬 <code>{chat_id}</code>\n"
        text += f"📨 Сообщений: {stats.get('messages', 0)}\n"
        text += f"👥 Пользователей: {stats.get('users', 0)}\n\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

def register(app):
    app.add_handler(CommandHandler("addchat", cmd_addchat))
    app.add_handler(CommandHandler("removechat", cmd_removechat))
    app.add_handler(CommandHandler("listchats", cmd_listchats))