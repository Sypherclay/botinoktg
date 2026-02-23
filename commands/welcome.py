"""
ПРИВЕТСТВЕННЫЕ СООБЩЕНИЯ
/setwelcome, /welcome, /welcomestatus, /showwelcome, /welcomereset
"""
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
from telegram import User
from database import (
    get_chat_welcome, set_chat_welcome,
    enable_chat_welcome, disable_chat_welcome,
    get_welcome_status, set_global_welcome_status
)
from permissions import is_admin, is_owner
from logger import log_admin_action

async def cmd_setwelcome(update, context):
    """Установить текст приветствия"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 <b>Установка приветствия</b>\n\n"
            "/setwelcome [текст]\n\n"
            "<b>Переменные:</b>\n"
            "• <code>{{user}}</code> - кликабельное имя\n"
            "• <code>{{user_name}}</code> - обычное имя\n"
            "• <code>{{mention}}</code> - @username\n"
            "• <code>{{id}}</code> - ID\n"
            "• <code>{{chat}}</code> - название чата\n\n"
            "Пример:\n"
            "<code>/setwelcome 👋 Привет, {{user}}!</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    chat_id = str(update.effective_chat.id)
    text = ' '.join(context.args)
    
    # Заменяем {{user}} на корректный формат для БД
    # В БД храним с {user}, но в команде используем {{user}} для экранирования
    db_text = text.replace('{{user}}', '{user}').replace('{{user_name}}', '{user_name}').replace('{{mention}}', '{mention}').replace('{{id}}', '{id}').replace('{{chat}}', '{chat}')
    
    set_chat_welcome(chat_id, db_text)
    
    # Предпросмотр
    from permissions import get_clickable_name
    test_user = User(id=123456789, first_name="Иван", is_bot=False, username="ivan")
    test_clickable = get_clickable_name(123456789, "Иван", "ivan")
    
    preview = text.replace('{{user}}', test_clickable)
    preview = preview.replace('{{user_name}}', "Иван Иванов")
    preview = preview.replace('{{mention}}', "@ivan")
    preview = preview.replace('{{id}}', "123456789")
    preview = preview.replace('{{chat}}', update.effective_chat.title or "чат")
    
    await update.message.reply_text(
        f"✅ Приветствие обновлено!\n\n📝 <b>Предпросмотр:</b>\n{preview}",
        parse_mode=ParseMode.HTML
    )
    
    log_admin_action(
        admin_id=update.effective_user.id,
        admin_name=update.effective_user.full_name,
        action="Изменил приветствие",
        target=chat_id
    )

async def cmd_welcome(update, context):
    """Включить/выключить приветствие для чата"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    chat_id = str(update.effective_chat.id)
    
    if not context.args:
        status = get_welcome_status(chat_id)
        text = f"📋 <b>Статус:</b> {'✅ Вкл' if status['chat_enabled'] else '❌ Выкл'}\n"
        text += f"<b>Глобально:</b> {'✅' if status['global_enabled'] else '❌'}\n"
        text += f"<b>Текст:</b> {status['message'][:100] if status['message'] else 'стандартный'}\n\n"
        text += "/welcome on - включить\n/welcome off - выключить"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
    
    action = context.args[0].lower()
    
    if action in ['on', 'вкл']:
        enable_chat_welcome(chat_id)
        await update.message.reply_text("✅ Приветствия включены для этого чата")
    elif action in ['off', 'выкл']:
        disable_chat_welcome(chat_id)
        await update.message.reply_text("✅ Приветствия выключены для этого чата")
    else:
        await update.message.reply_text("/welcome on или /welcome off")

async def cmd_welcomestatus(update, context):
    """Глобальное включение/выключение"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Только для владельца")
        return
    
    if not context.args:
        status = get_welcome_status(str(update.effective_chat.id))
        global_status = "✅ Вкл" if status['global_enabled'] else "❌ Выкл"
        await update.message.reply_text(
            f"🌍 <b>Глобальный статус:</b> {global_status}\n\n"
            f"/welcomestatus on - включить\n/welcomestatus off - выключить",
            parse_mode=ParseMode.HTML
        )
        return
    
    action = context.args[0].lower()
    
    if action in ['on', 'вкл']:
        set_global_welcome_status(True)
        await update.message.reply_text("✅ Приветствия включены глобально")
    elif action in ['off', 'выкл']:
        set_global_welcome_status(False)
        await update.message.reply_text("✅ Приветствия выключены глобально")
    else:
        await update.message.reply_text("/welcomestatus on или off")

async def cmd_showwelcome(update, context):
    """Показать настройки приветствия"""
    chat_id = str(update.effective_chat.id)
    status = get_welcome_status(chat_id)
    
    final = "✅ Вкл" if (status['global_enabled'] and status['chat_enabled']) else "❌ Выкл"
    details = []
    if not status['global_enabled']:
        details.append("глобально выключено")
    elif not status['chat_enabled']:
        details.append("выключено для чата")
    
    text = f"📋 <b>Приветствия:</b> {final}\n"
    if details:
        text += f"<i>({', '.join(details)})</i>\n"
    text += f"\n<b>Текст:</b>\n{status['message'] or 'стандартный'}"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def cmd_welcomereset(update, context):
    """Сбросить к стандартному тексту"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    chat_id = str(update.effective_chat.id)
    set_chat_welcome(chat_id, None)
    
    await update.message.reply_text("✅ Приветствие сброшено к стандартному")

def register(app):
    app.add_handler(CommandHandler("setwelcome", cmd_setwelcome))
    app.add_handler(CommandHandler("welcome", cmd_welcome))
    app.add_handler(CommandHandler("welcomestatus", cmd_welcomestatus))
    app.add_handler(CommandHandler("showwelcome", cmd_showwelcome))
    app.add_handler(CommandHandler("welcomereset", cmd_welcomereset))