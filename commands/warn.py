"""
КОМАНДЫ ВЫГОВОРОВ - СТАБИЛЬНАЯ ВЕРСИЯ
!выговор, !лист, !снять выговор, !мои выговоры
"""
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
from datetime import datetime
import traceback
from database import (
    add_warning, get_all_users_with_warnings, get_warnings_count,
    remove_last_warning, get_user_max_warnings, get_user_rank_db,
    get_user_warnings
)
from permissions import has_permission, get_clickable_name
from user_resolver import resolve_user
from constants import RANKS, ANONYMOUS_ADMIN_ID
from logger import log_warning_issued, log_command

print("✅ warn.py загружен!")

async def cmd_warn(update, context):
    """!выговор [причина] - выдать выговор (поддерживает @user и reply)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !выговор")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not has_permission(user_id, '!выговор'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        # Получаем текст сообщения
        message_text = update.message.text
        parts = message_text.split(maxsplit=2)
        
        # Определяем причину
        reason = "Нарушение правил"
        
        # Сохраняем аргументы для resolve_user
        if len(parts) > 1:
            context.args = [parts[1]]
        else:
            context.args = []
        
        # Ищем пользователя (приоритет: reply > аргументы)
        user = await resolve_user(update, context, required=True, allow_self=False)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        # Проверка на анонимного админа
        if user.id == ANONYMOUS_ADMIN_ID:
            await update.message.reply_text("❌ Нельзя выдать выговор анонимному администратору")
            return
        
        # Если есть причина в третьем аргументе
        if len(parts) > 2:
            reason = parts[2]
        # Если есть причина и это ответ на сообщение
        elif len(parts) > 1 and update.message.reply_to_message:
            reason = parts[1]
        
        print(f"   reason: {reason}")
        
        # Проверка ранга цели
        target_rank = get_user_rank_db(user.id)
        if target_rank in ['owner', 'curator', 'custom', 'helper_plus']:
            rank_name = RANKS.get(target_rank, {}).get('name', '')
            await update.message.reply_text(f"❌ Пользователь с рангом '{rank_name}' не может получить выговор")
            return
        
        # Выдаём выговор
        warning_count = add_warning(
            user.id, chat_id, reason,
            user_id, update.effective_user.full_name
        )
        max_warnings = get_user_max_warnings(user.id)
        
        clickable = get_clickable_name(user.id, user.first_name, user.username)
        
        response = f"⚠️ {clickable} получает выговор\n🫡 Причина: {reason}\n📊 Выговоров: {warning_count}/{max_warnings}"
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        print(f"✅ Выговор выдан, теперь {warning_count}/{max_warnings}")
        
        log_warning_issued(
            admin_id=user_id,
            admin_name=update.effective_user.full_name,
            user_id=user.id,
            user_name=user.full_name,
            reason=reason
        )
        
        log_command(
            "!выговор", user_id, update.effective_user.full_name,
            chat_id, f"Цель: {user.id}, Причина: {reason}"
        )
        
        # Проверка на кик
        if warning_count >= max_warnings:
            from commands.kick import kick_user
            await kick_user(update, context, user, "Превышение лимита выговоров")
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_warn_list(update, context):
    """!лист - список всех выговоров"""
    print("\n🔥 ВЫПОЛНЕНИЕ !лист")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   user_id: {user_id}")
        
        if not has_permission(user_id, '!лист'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        users = get_all_users_with_warnings(chat_id)
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей с выговорами")
            return
        
        warnings_list = []
        for uid, name, username, warning_count in users:
            # Проверяем ранг
            rank = get_user_rank_db(uid)
            if rank in ['owner', 'curator']:
                continue
            
            clickable = get_clickable_name(uid, name, username)
            max_w = get_user_max_warnings(uid)
            warnings_list.append(f"📝 {clickable} - {warning_count}/{max_w}")
        
        response = "📋 <b>СПИСОК ВЫГОВОРОВ</b>\n\n" + "\n".join(warnings_list)
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        print("✅ Список выговоров отправлен")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_warn_list: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_my_warnings(update, context):
    """!мои выговоры - показать свои активные выговоры (ТОЛЬКО ДЛЯ СЕБЯ)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !мои выговоры")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   user_id: {user_id}")
        
        # Игнорируем любые аргументы - показываем только себя
        target_id = user_id
        target_user = update.effective_user
        
        warning_count = get_warnings_count(target_id, chat_id)
        max_warnings = get_user_max_warnings(target_id)
        
        clickable = get_clickable_name(target_id, target_user.first_name, target_user.username)
        
        # Получаем активные выговоры с деталями
        active_warnings = get_user_warnings(target_id, chat_id, active_only=True)
        
        lines = []
        lines.append(f"📊 <b>Ваши выговоры</b> — {clickable}")
        lines.append(f"⚠️ <b>Всего выговоров:</b> {warning_count}/{max_warnings}")
        lines.append("")
        lines.append("🔥 <b>Активные выговоры</b>")
        
        if active_warnings:
            for i, record in enumerate(active_warnings, 1):
                # record: id, reason, warned_by_name, date, warned_by
                reason = record[1] or 'Не указана'
                admin_name = record[2] or 'Неизвестно'
                date = datetime.fromisoformat(record[3]).strftime("%d.%m.%Y %H:%M")
                
                lines.append("")
                lines.append(f"⚠️ <b>Выговор #{i}</b>")
                lines.append(f"📝 За: {reason}")
                lines.append(f"👮 Выдал: {admin_name}")
                lines.append(f"📅 Дата: {date}")
        else:
            lines.append("")
            lines.append("✨ У вас нет активных выговоров")
        
        await update.message.reply_text(
            "\n".join(lines), 
            parse_mode=ParseMode.HTML, 
            reply_to_message_id=update.message.message_id
        )
        print("✅ Информация о выговорах отправлена")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_my_warnings: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_remove_warn(update, context):
    """!снять выговор - снять последний выговор (поддерживает @user, ID и reply)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !снять выговор")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not has_permission(user_id, '!снять выговор'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        # Получаем текст сообщения
        message_text = update.message.text
        parts = message_text.split()
        
        # Сохраняем аргументы для resolve_user (все, кроме первого слова)
        if len(parts) > 1:
            # Проверяем, что второй аргумент не равен "выговор"
            if parts[1].lower() != 'выговор':
                context.args = [parts[1]]
                print(f"   аргумент для resolve_user: {context.args}")
            else:
                context.args = []
        else:
            context.args = []
        
        # Ищем пользователя (приоритет: reply > аргументы)
        user = await resolve_user(update, context, required=True, allow_self=False)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        if user.id == ANONYMOUS_ADMIN_ID:
            await update.message.reply_text("❌ Нельзя снять выговор анонимному администратору")
            return
        
        removed = remove_last_warning(
            user.id, chat_id,
            user_id, update.effective_user.full_name
        )
        
        if not removed:
            await update.message.reply_text(f"ℹ️ У пользователя нет активных выговоров")
            return
        
        count = get_warnings_count(user.id, chat_id)
        max_w = get_user_max_warnings(user.id)
        clickable = get_clickable_name(user.id, user.first_name, user.username)
        
        await update.message.reply_text(
            f"✅ У {clickable} снят 1 выговор\n📊 Выговоров: {count}/{max_w}",
            parse_mode=ParseMode.HTML
        )
        print(f"✅ Выговор снят, осталось {count}/{max_w}")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_remove_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд warn.py...")
    app.add_handler(MessageHandler(filters.Regex(r'^!выговор\b'), cmd_warn))
    app.add_handler(MessageHandler(filters.Regex(r'^!лист\b'), cmd_warn_list))
    app.add_handler(MessageHandler(filters.Regex(r'^!мои выговоры\b'), cmd_my_warnings))
    app.add_handler(MessageHandler(filters.Regex(r'^!снять выговор\b'), cmd_remove_warn))
    print("✅ warn.py зарегистрирован")