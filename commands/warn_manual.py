"""
РУЧНЫЕ ВАРНЫ - ИСПРАВЛЕННАЯ ВЕРСИЯ
!варн, !снять варн, !варнлист
"""
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
import sqlite3
import traceback
from database import (
    get_auto_warn_count, increment_auto_warn_count, reset_auto_warn_count,
    add_warning, get_warnings_count, get_user_max_warnings,
    get_auto_warn_message, get_user_rank_db, DB_PATH
)
from permissions import has_permission, get_clickable_name
from user_resolver import resolve_user
from constants import RANKS, ANONYMOUS_ADMIN_ID
from logger import log_command

print("✅ warn_manual.py загружен!")

async def cmd_add_warn(update, context):
    """!варн [причина] - выдать ручной варн"""
    print("\n🔥 ВЫПОЛНЕНИЕ !варн")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not has_permission(user_id, '!варн'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        # Получаем причину из текста
        message_text = update.message.text
        parts = message_text.split(maxsplit=2)
        
        # Сохраняем аргументы для resolve_user
        if len(parts) > 1:
            context.args = [parts[1]]
        
        user = await resolve_user(update, context)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        if user.id == ANONYMOUS_ADMIN_ID:
            await update.message.reply_text("❌ Нельзя выдать варн анонимному администратору")
            return
        
        # Проверка ранга
        rank = get_user_rank_db(user.id)
        if rank in ['owner', 'curator', 'custom', 'helper_plus']:
            await update.message.reply_text(f"❌ Пользователь не может получить варн")
            return
        
        # Определяем причину
        reason = "Ручной варн"
        if len(parts) > 2:
            reason = parts[2]
        elif len(parts) > 1 and update.message.reply_to_message:
            reason = parts[1]
        
        print(f"   reason: {reason}")
        
        # Увеличиваем счётчик варнов
        current_count = increment_auto_warn_count(user.id, chat_id)
        
        # Отправляем сообщение
        warn_message = get_auto_warn_message()
        admin_name = update.effective_user.full_name
        
        await update.message.reply_text(
            f"{warn_message}\n\n👮 Выдал: {admin_name}",
            reply_to_message_id=update.message.message_id
        )
        
        log_command(
            "!варн", user_id, admin_name,
            chat_id, f"Цель: {user.id}, Всего: {current_count}"
        )
        
        print(f"⚠️ Варн выдан, всего: {current_count}")
        
        # Проверка на 3 варна
        if current_count >= 3:
            reset_auto_warn_count(user.id, chat_id)
            
            warning_count = add_warning(
                user.id, chat_id,
                f"3 варна: {reason}",
                0, "Система"
            )
            max_warnings = get_user_max_warnings(user.id)
            
            clickable = get_clickable_name(user.id, user.first_name, user.username)
            await update.message.reply_text(
                f"⚠️ {clickable} получает выговор (3 варна)\n📊 Выговоров: {warning_count}/{max_warnings}",
                parse_mode=ParseMode.HTML
            )
            print(f"⚠️ 3 варна -> выговор {warning_count}/{max_warnings}")
            
            # Проверка на кик
            if warning_count >= max_warnings:
                from commands.kick import kick_user
                await kick_user(update, context, user, "3 варна → выговор → лимит")
                
    except Exception as e:
        print(f"❌ Ошибка в cmd_add_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_remove_warn(update, context):
    """!снять варн - снять все варны"""
    print("\n🔥 ВЫПОЛНЕНИЕ !снять варн")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not has_permission(user_id, '!снять варн'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        # Получаем цель из аргументов
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) > 1:
            context.args = parts[1:]
        
        user = await resolve_user(update, context)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        current_count = get_auto_warn_count(user.id, chat_id)
        
        if current_count <= 0:
            await update.message.reply_text("ℹ️ У пользователя нет активных варнов")
            return
        
        reset_auto_warn_count(user.id, chat_id)
        
        admin_name = update.effective_user.full_name
        clickable = get_clickable_name(user.id, user.first_name, user.username)
        
        await update.message.reply_text(
            f"✅ {clickable} сняты все варны ({current_count} шт.)\n👮 Администратор: {admin_name}",
            parse_mode=ParseMode.HTML
        )
        print(f"✅ Снято варнов: {current_count}")
        
        log_command(
            "!снять варн", user_id, admin_name,
            chat_id, f"Цель: {user.id}, Снято: {current_count}"
        )
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_remove_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_warn_list(update, context):
    """!варнлист - список пользователей с варнами"""
    print("\n🔥 ВЫПОЛНЕНИЕ !варнлист")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   user_id: {user_id}")
        
        if not has_permission(user_id, '!варнлист'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.user_id, a.count, u.name, u.username
            FROM auto_warn_counts a
            LEFT JOIN users u ON a.user_id = u.user_id AND a.chat_id = u.chat_id
            WHERE a.chat_id = ? AND a.count > 0
            ORDER BY a.count DESC
        ''', (chat_id,))
        
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей с активными варнами")
            return
        
        warn_list = []
        total = 0
        
        for uid, count, name, username in users:
            clickable = get_clickable_name(uid, name or f"User {uid}", username or "")
            warn_list.append(f"⚠️ {clickable} — {count}")
            total += count
        
        response = f"📋 <b>СПИСОК АКТИВНЫХ ВАРНОВ</b>\n"
        response += f"👥 Пользователей: {len(users)}\n"
        response += f"⚠️ Всего варнов: {total}\n\n"
        response += "\n".join(warn_list)
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        print("✅ Список варнов отправлен")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_warn_list: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд warn_manual.py...")
    app.add_handler(MessageHandler(filters.Regex(r'^!варн\b'), cmd_add_warn))
    app.add_handler(MessageHandler(filters.Regex(r'^!снять варн\b'), cmd_remove_warn))
    app.add_handler(MessageHandler(filters.Regex(r'^!варнлист\b'), cmd_warn_list))
    print("✅ warn_manual.py зарегистрирован")