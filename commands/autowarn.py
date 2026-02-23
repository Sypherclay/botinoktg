"""
УПРАВЛЕНИЕ АВТО-ВАРНАМИ - ИСПРАВЛЕННАЯ ВЕРСИЯ
/autowarn
"""
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
import traceback
from database import (
    get_auto_warn_topics, add_auto_warn_topic, remove_auto_warn_topic,
    get_whitelist, add_to_whitelist_db, remove_from_whitelist_db,
    get_auto_warn_message, set_auto_warn_message,
    get_user_info
)
from permissions import is_admin
from logger import log_admin_action

print("✅ autowarn.py загружен!")

async def cmd_autowarn(update, context):
    """Управление авто-варнами"""
    print("\n🔥 ВЫПОЛНЕНИЕ /autowarn")
    
    try:
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
        print(f"   команда: {cmd}")
        
        if cmd == "add_topic" and len(context.args) > 1:
            tid = context.args[1]
            print(f"   topic_id: {tid}")
            
            if tid not in get_auto_warn_topics():
                add_auto_warn_topic(tid)
                await update.message.reply_text(f"✅ Тема {tid} добавлена")
                print(f"✅ Тема {tid} добавлена")
            else:
                await update.message.reply_text(f"ℹ️ Уже есть")
        
        elif cmd == "remove_topic" and len(context.args) > 1:
            tid = context.args[1]
            print(f"   topic_id: {tid}")
            
            if tid in get_auto_warn_topics():
                remove_auto_warn_topic(tid)
                await update.message.reply_text(f"✅ Тема {tid} удалена")
                print(f"✅ Тема {tid} удалена")
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
            print(f"📋 Список тем отправлен")
        
        elif cmd == "add_whitelist" and len(context.args) > 1:
            try:
                uid = int(context.args[1])
                print(f"   user_id: {uid}")
                
                if uid not in get_whitelist():
                    add_to_whitelist_db(uid)
                    await update.message.reply_text(f"✅ Пользователь {uid} добавлен в белый список")
                    print(f"✅ Пользователь {uid} добавлен в белый список")
                else:
                    await update.message.reply_text(f"ℹ️ Уже есть")
            except ValueError:
                await update.message.reply_text("❌ ID должен быть числом")
        
        elif cmd == "remove_whitelist" and len(context.args) > 1:
            try:
                uid = int(context.args[1])
                print(f"   user_id: {uid}")
                
                if uid in get_whitelist():
                    remove_from_whitelist_db(uid)
                    await update.message.reply_text(f"✅ Пользователь {uid} удалён")
                    print(f"✅ Пользователь {uid} удалён из белого списка")
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
            print(f"👥 Белый список отправлен")
        
        elif cmd == "set_message" and len(context.args) > 1:
            msg = ' '.join(context.args[1:])
            set_auto_warn_message(msg)
            await update.message.reply_text(f"✅ Сообщение обновлено:\n\n{msg}")
            print(f"✅ Сообщение обновлено")
        
        elif cmd == "show_message":
            msg = get_auto_warn_message()
            await update.message.reply_text(f"📝 <b>Сообщение:</b>\n\n{msg}", parse_mode='HTML')
            print(f"📝 Сообщение показано")
        
        else:
            await update.message.reply_text("❌ Неизвестная команда. /autowarn для справки")
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_autowarn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

# Функция для обработки авто-варна (вызывается из message_handler)
async def process_auto_warn(update, context, user_id, has_media, has_text):
    """Обработка авто-варна"""
    try:
        from database import (
            get_auto_warn_message, increment_auto_warn_count,
            reset_auto_warn_count, add_warning, get_user_max_warnings,
            get_user_info, get_user_custom_nick
        )
        from permissions import get_clickable_name
        from commands.kick import kick_user
        
        chat_id = str(update.effective_chat.id)
        
        info = get_user_info(user_id, chat_id)
        name = info[0] if info else update.effective_user.first_name
        username = info[1] if info else update.effective_user.username
        
        custom = get_user_custom_nick(user_id)
        display = custom if custom else name
        
        warn_msg = get_auto_warn_message()
        await update.message.reply_text(
            warn_msg,
            reply_to_message_id=update.message.message_id
        )
        
        count = increment_auto_warn_count(user_id, chat_id)
        
        from logger import log_auto_warn
        log_auto_warn(user_id, display, has_media, has_text, count)
        
        if count >= 3:
            reset_auto_warn_count(user_id, chat_id)
            
            warn_count = add_warning(
                user_id, chat_id,
                "Некорректная подача отчетности",
                0, "Авто-система"
            )
            
            max_w = get_user_max_warnings(user_id)
            
            clickable = get_clickable_name(user_id, display, username)
            
            await update.message.reply_text(
                f"⚠️ {clickable} получает автоматический выговор\n"
                f"📊 Выговоров: {warn_count}/{max_w}",
                parse_mode='HTML'
            )
            
            if warn_count >= max_w:
                await kick_user(update, context, update.effective_user, "Лимит выговоров")
                
    except Exception as e:
        print(f"❌ Ошибка в process_auto_warn: {e}")
        traceback.print_exc()

def register(app):
    print("📝 Регистрация команд autowarn.py...")
    app.add_handler(CommandHandler("autowarn", cmd_autowarn))
    print("✅ autowarn.py зарегистрирован")