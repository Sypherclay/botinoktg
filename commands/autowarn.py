"""
УПРАВЛЕНИЕ АВТО-ВАРНАМИ
/autowarn
"""
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
from database import (
    get_auto_warn_topics, add_auto_warn_topic, remove_auto_warn_topic,
    get_whitelist, add_to_whitelist_db, remove_from_whitelist_db,
    get_auto_warn_message, set_auto_warn_message,
    get_user_info
)
from permissions import is_admin
from logger import log_admin_action

async def cmd_autowarn(update, context):
    """Управление авто-варнами"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    if not context.args:
        help_text = (
            "⚠️ <b>Авто-варны</b>\n\n"
            "<b>Команды:</b>\n"
            "➕ /autowarn add_topic ID - добавить тему\n"
            "➖ /autowarn remove_topic ID - удалить тему\n"
            "📋 /autowarn list_topics - список тем\n"
            "✅ /autowarn add_whitelist ID - добавить в белый список\n"
            "🗑️ /autowarn remove_whitelist ID - удалить\n"
            "👥 /autowarn list_whitelist - белый список\n"
            "✏️ /autowarn set_message ТЕКСТ - установить сообщение\n"
            "👁️ /autowarn show_message - показать сообщение\n\n"
            "<b>Логика:</b>\n"
            "📷 Только медиа → варн\n"
            "📝 Только текст → варн\n"
            "✅ Текст+медиа → OK\n"
            "⚠️ 3 варна = 1 выговор"
        )
        await update.message.reply_text(help_text, parse_mode='HTML')
        return
    
    cmd = context.args[0].lower()
    
    if cmd == "add_topic" and len(context.args) > 1:
        tid = context.args[1]
        if tid not in get_auto_warn_topics():
            add_auto_warn_topic(tid)
            await update.message.reply_text(f"✅ Тема {tid} добавлена")
        else:
            await update.message.reply_text(f"ℹ️ Уже есть")
    
    elif cmd == "remove_topic" and len(context.args) > 1:
        tid = context.args[1]
        if tid in get_auto_warn_topics():
            remove_auto_warn_topic(tid)
            await update.message.reply_text(f"✅ Тема {tid} удалена")
        else:
            await update.message.reply_text(f"❌ Не найдена")
    
    elif cmd == "list_topics":
        topics = get_auto_warn_topics()
        if topics:
            text = "📋 <b>Темы с авто-варнами:</b>\n\n" + "\n".join([f"📌 <code>{t}</code>" for t in topics])
            text += f"\n\n📊 Всего: {len(topics)}"
        else:
            text = "📭 Нет тем"
        await update.message.reply_text(text, parse_mode='HTML')
    
    elif cmd == "add_whitelist" and len(context.args) > 1:
        try:
            uid = int(context.args[1])
            if uid not in get_whitelist():
                add_to_whitelist_db(uid)
                await update.message.reply_text(f"✅ Пользователь {uid} добавлен в белый список")
            else:
                await update.message.reply_text(f"ℹ️ Уже есть")
        except ValueError:
            await update.message.reply_text("❌ ID должен быть числом")
    
    elif cmd == "remove_whitelist" and len(context.args) > 1:
        try:
            uid = int(context.args[1])
            if uid in get_whitelist():
                remove_from_whitelist_db(uid)
                await update.message.reply_text(f"✅ Пользователь {uid} удалён")
            else:
                await update.message.reply_text(f"❌ Не найден")
        except ValueError:
            await update.message.reply_text("❌ ID должен быть числом")
    
    elif cmd == "list_whitelist":
        wl = get_whitelist()
        if wl:
            lines = ["👥 <b>Белый список:</b>\n"]
            for uid in wl:
                info = get_user_info(uid, str(update.effective_chat.id))
                name = info[0] if info else f"User {uid}"
                lines.append(f"• {name} (<code>{uid}</code>)")
            lines.append(f"\n📊 Всего: {len(wl)}")
            await update.message.reply_text("\n".join(lines), parse_mode='HTML')
        else:
            await update.message.reply_text("📭 Белый список пуст")
    
    elif cmd == "set_message" and len(context.args) > 1:
        msg = ' '.join(context.args[1:])
        set_auto_warn_message(msg)
        await update.message.reply_text(f"✅ Сообщение обновлено:\n\n{msg}")
    
    elif cmd == "show_message":
        msg = get_auto_warn_message()
        await update.message.reply_text(f"📝 <b>Сообщение:</b>\n\n{msg}", parse_mode='HTML')
    
    else:
        await update.message.reply_text("❌ Неизвестная команда. /autowarn для справки")

def register(app):
    app.add_handler(CommandHandler("autowarn", cmd_autowarn))