"""
ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЯХ - ИСПРАВЛЕННАЯ ВЕРСИЯ
!инфа, !кто админ - с поддержкой @user
"""
from datetime import datetime
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
import sqlite3
import traceback
from database import (
    get_user_info, get_user_custom_nick, get_user_rank_db,
    get_warnings_count, get_user_max_warnings,
    get_vacation_info, get_user_balance, get_setting,
    get_user_rewards, DB_PATH
)
from permissions import get_clickable_name
from user_resolver import resolve_user
from constants import RANKS

print("✅ info.py загружен!")

def get_top_user(chat_id, field):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'SELECT user_id FROM users WHERE chat_id = ? ORDER BY {field} DESC LIMIT 1', (chat_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
    except Exception as e:
        print(f"❌ Ошибка в get_top_user: {e}")
        return None

def get_top_balance(chat_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.user_id FROM salary s
            JOIN users u ON s.user_id = u.user_id
            WHERE u.chat_id = ?
            ORDER BY s.balance DESC LIMIT 1
        ''', (chat_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
    except Exception as e:
        print(f"❌ Ошибка в get_top_balance: {e}")
        return None

async def cmd_who_admin(update, context):
    """Команда !кто админ"""
    print("\n🔥 ВЫПОЛНЕНИЕ !кто админ")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        owners, curators, deputies, managers, moders, customs, helpers = [], [], [], [], [], [], []
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, rank FROM ranks')
        ranks = cursor.fetchall()
        conn.close()
        
        for uid, rank in ranks:
            if rank in ['owner', 'curator', 'deputy_curator', 'manager', 'moder', 'custom', 'helper_plus']:
                info = get_user_info(uid, chat_id)
                name = info[0] if info and info[0] else f"User {uid}"
                username = info[1] if info and info[1] else ""
                custom = get_user_custom_nick(uid)
                display = custom if custom else name
                clickable = get_clickable_name(uid, display, username)
                
                if rank == 'owner':
                    owners.append(f"🔹 {clickable}")
                elif rank == 'curator':
                    curators.append(f"🔹 {clickable}")
                elif rank == 'deputy_curator':
                    deputies.append(f"🔹 {clickable}")
                elif rank == 'manager':
                    managers.append(f"🔹 {clickable}")
                elif rank == 'moder':
                    moders.append(f"🔹 {clickable}")
                elif rank == 'custom':
                    customs.append(f"🔹 {clickable}")
                elif rank == 'helper_plus':
                    helpers.append(f"🔹 {clickable}")
        
        response = ""
        if owners:
            response += "<b>✨✨✨✨✨ Владелец</b>\n" + "\n".join(owners) + "\n\n"
        if curators:
            response += "<b>✨✨✨✨ Куратор</b>\n" + "\n".join(curators) + "\n\n"
        if deputies:
            response += "<b>✨✨✨ Зам Куратора</b>\n" + "\n".join(deputies) + "\n\n"
        if managers:
            response += "<b>✨✨ Руководитель</b>\n" + "\n".join(managers) + "\n\n"
        if moders:
            response += "<b>✨ Модер</b>\n" + "\n".join(moders) + "\n\n"
        if customs:
            response += "<b>🔱🔱🔱🔱🔱 Custom</b>\n" + "\n".join(customs) + "\n\n"
        if helpers:
            response += "<b>💸💸💸 Хелпер+</b>\n" + "\n".join(helpers) + "\n\n"
        
        if not response:
            response = "📭 Нет администраторов с рангами"
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML, reply_to_message_id=update.message.message_id)
        print("✅ !кто админ выполнен")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_who_admin: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_info(update, context):
    """Команда !инфа - информация о пользователе (с поддержкой @user)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !инфа")
    print(f"   Текст: {update.message.text}")
    
    try:
        chat_id = str(update.effective_chat.id)
        print(f"   chat_id: {chat_id}")
        
        # Определяем, нужно ли искать другого пользователя
        message_text = update.message.text
        parts = message_text.split()
        
        # Если есть аргументы или это ответ на сообщение
        if len(parts) > 1 or update.message.reply_to_message:
            print("   🔍 Поиск целевого пользователя...")
            
            # Сохраняем аргументы для resolve_user
            if len(parts) > 1:
                context.args = parts[1:]
            
            user = await resolve_user(update, context, required=True, allow_self=False)
            if not user:
                return
        else:
            # Если нет аргументов - показываем себя
            user = update.effective_user
            print(f"   Показываем себя: {user.id}")
        
        print(f"✅ user: ID={user.id}, имя={user.first_name}")
        
        # Получаем информацию о пользователе
        info = get_user_info(user.id, chat_id)
        
        if info and isinstance(info, tuple) and len(info) >= 2:
            name = info[0] if info[0] else user.first_name
            username = info[1] if info[1] else user.username
        else:
            name = user.first_name
            username = user.username
        
        custom = get_user_custom_nick(user.id)
        display = custom if custom else name
        clickable = get_clickable_name(user.id, display, username)
        
        rank = get_user_rank_db(user.id)
        rank_name = RANKS.get(rank, {}).get('name', 'Участник')
        warnings = get_warnings_count(user.id, chat_id)
        max_w = int(get_setting('max_warnings', '3'))
        immunity = rank in ['owner', 'curator', 'custom', 'helper_plus']
        
        vacation = get_vacation_info(user.id)
        used_days = 0
        limit = int(get_setting('max_vacation_days', '14'))
        vacation_status = "нет"
        
        if vacation and isinstance(vacation, tuple) and len(vacation) >= 3:
            used_days = vacation[2] if vacation[2] else 0
            try:
                if datetime.now() <= datetime.fromisoformat(vacation[1]):
                    vacation_status = f"до {datetime.fromisoformat(vacation[1]).strftime('%d.%m.%Y')}"
            except:
                pass
        
        balance = get_user_balance(user.id)
        
        response = f"👤 <b>Пользователь:</b> {clickable}\n"
        response += f"🎖️ <b>Должность:</b> {rank_name}\n\n"
        
        if immunity:
            response += f"⚠️ <b>Выговоры:</b> 🛡️ ИММУНИТЕТ\n"
        else:
            response += f"⚠️ <b>Выговоры:</b> {warnings}/{max_w}\n"
        
        response += f"🏖️ <b>Отпуск:</b> {used_days}/{limit} дней"
        if vacation_status != "нет":
            response += f"\n📅 <b>В отпуске:</b> {vacation_status}"
        else:
            response += f"\n📅 <b>В отпуске:</b> нет"
        
        response += f"\n💰 <b>Баланс:</b> {balance} HC"
        response += f"\n\n🆔 <b>ID:</b> <code>{user.id}</code>"
        if user.username:
            response += f"\n🌐 <b>Username:</b> @{user.username}"
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        print("✅ !инфа выполнена")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_info: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд info.py...")
    app.add_handler(MessageHandler(filters.Regex(r'^!кто админ$'), cmd_who_admin))
    app.add_handler(MessageHandler(filters.Regex(r'^!инфа\b'), cmd_info))  # \b чтобы ловило и !инфа и !инфа @user
    app.add_handler(MessageHandler(filters.Regex(r'^!info\b'), cmd_info))
    print("✅ info.py зарегистрирован")