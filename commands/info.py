"""
ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЯХ - ДИАГНОСТИЧЕСКАЯ ВЕРСИЯ
!инфа, !кто админ
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
    print(f"🔍 get_top_user: chat_id={chat_id}, field={field}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'SELECT user_id FROM users WHERE chat_id = ? ORDER BY {field} DESC LIMIT 1', (chat_id,))
        res = cursor.fetchone()
        conn.close()
        print(f"   результат: {res[0] if res else None}")
        return res[0] if res else None
    except Exception as e:
        print(f"❌ Ошибка в get_top_user: {e}")
        traceback.print_exc()
        return None

def get_top_balance(chat_id):
    print(f"🔍 get_top_balance: chat_id={chat_id}")
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
        print(f"   результат: {res[0] if res else None}")
        return res[0] if res else None
    except Exception as e:
        print(f"❌ Ошибка в get_top_balance: {e}")
        traceback.print_exc()
        return None

async def cmd_who_admin(update, context):
    """Команда !кто админ"""
    print("\n" + "="*50)
    print("🔥 ВЫПОЛНЕНИЕ КОМАНДЫ !кто админ")
    print("="*50)
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        print(f"   user_id: {user_id}")
        print(f"   chat_id: {chat_id}")
        
        owners, curators, deputies, managers, moders, customs, helpers = [], [], [], [], [], [], []
        
        print("📊 Запрос к таблице ranks...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, rank FROM ranks')
        ranks = cursor.fetchall()
        conn.close()
        print(f"   получено записей: {len(ranks)}")
        
        for uid, rank in ranks:
            if rank in ['owner', 'curator', 'deputy_curator', 'manager', 'moder', 'custom', 'helper_plus']:
                info = get_user_info(uid, chat_id)
                name = info[0] if info else f"User {uid}"
                username = info[1] if info else ""
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
        
        print(f"   owners: {len(owners)}")
        print(f"   curators: {len(curators)}")
        print(f"   deputies: {len(deputies)}")
        print(f"   managers: {len(managers)}")
        print(f"   moders: {len(moders)}")
        print(f"   customs: {len(customs)}")
        print(f"   helpers: {len(helpers)}")
        
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
        
        print("📤 Отправка ответа в Telegram...")
        print(f"   длина ответа: {len(response)} символов")
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML, reply_to_message_id=update.message.message_id)
        
        print("✅ Ответ успешно отправлен!")
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_info(update, context):
    """Команда !инфа"""
    print("\n" + "="*50)
    print("🔥 ВЫПОЛНЕНИЕ КОМАНДЫ !инфа")
    print("="*50")
    
    try:
        print(f"   Текст команды: {update.message.text}")
        print(f"   От пользователя: {update.effective_user.id} - {update.effective_user.first_name}")
        
        chat_id = str(update.effective_chat.id)
        print(f"   chat_id: {chat_id}")
        
        print("🔍 Вызов resolve_user...")
        user = await resolve_user(update, context, required=False, allow_self=True)
        
        if not user:
            print("❌ resolve_user вернул None - выход")
            return
        
        print(f"✅ resolve_user успешно: user.id={user.id}, user.first_name={user.first_name}")
        
        print("🔍 Получение информации о пользователе...")
        info = get_user_info(user.id, chat_id)
        print(f"   get_user_info: {info}")
        
        name = info[0] if info else user.first_name
        username = info[1] if info else user.username
        custom = get_user_custom_nick(user.id)
        display = custom if custom else name
        print(f"   name: {name}, username: {username}, custom: {custom}, display: {display}")
        
        print("🔍 Получение clickable_name...")
        clickable = get_clickable_name(user.id, display, username)
        print(f"   clickable: {clickable}")
        
        print("🔍 Получение ранга...")
        rank = get_user_rank_db(user.id)
        rank_name = RANKS.get(rank, {}).get('name', 'Участник')
        print(f"   rank: {rank}, rank_name: {rank_name}")
        
        print("🔍 Получение выговоров...")
        warnings = get_warnings_count(user.id, chat_id)
        max_w = int(get_setting('max_warnings', '3'))
        immunity = rank in ['owner', 'curator', 'custom', 'helper_plus']
        print(f"   warnings: {warnings}, max_w: {max_w}, immunity: {immunity}")
        
        print("🔍 Получение отпусков...")
        vacation = get_vacation_info(user.id)
        used_days = vacation[2] if vacation else 0
        limit = int(get_setting('max_vacation_days', '14'))
        print(f"   vacation: {vacation}, used_days: {used_days}, limit: {limit}")
        
        vacation_status = "нет"
        if vacation and datetime.now() <= datetime.fromisoformat(vacation[1]):
            vacation_status = f"до {datetime.fromisoformat(vacation[1]).strftime('%d.%m.%Y')}"
        print(f"   vacation_status: {vacation_status}")
        
        print("🔍 Получение баланса...")
        balance = get_user_balance(user.id)
        print(f"   balance: {balance}")
        
        print("🔍 Получение топ-позиций...")
        top_activity = get_top_user(chat_id, 'count')
        top_punish = get_top_user(chat_id, 'punishments')
        top_balance = get_top_balance(chat_id)
        print(f"   top_activity: {top_activity}")
        print(f"   top_punish: {top_punish}")
        print(f"   top_balance: {top_balance}")
        
        badges = []
        if user.id == top_activity:
            badges.append("🏆 ТОП-1 Актив")
        if user.id == top_punish:
            badges.append("👑 ТОП-1 Наказания")
        if user.id == top_balance:
            badges.append("💎 ТОП-1 Баланс")
        print(f"   badges: {badges}")
        
        print("🔍 Получение наград...")
        rewards = get_user_rewards(user.id)
        reward_badges = ['💸 ЗА ДЕНЬГИ ДА' if '10_complaints' in rewards else '']
        reward_badges = [r for r in reward_badges if r]
        print(f"   rewards: {rewards}")
        print(f"   reward_badges: {reward_badges}")
        
        print("📝 Формирование ответа...")
        response = f"👤 <b>Пользователь:</b> {clickable}\n"
        response += f"🎖️ <b>Должность:</b> {rank_name}\n\n"
        
        if badges:
            response += f"{' | '.join(badges)}\n\n"
        
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
        
        if reward_badges:
            response += f"\n\n🎁 <b>Ачивки:</b> {' | '.join(reward_badges)}"
        
        response += f"\n\n🆔 <b>ID:</b> <code>{user.id}</code>"
        if user.username:
            response += f"\n🌐 <b>Username:</b> @{user.username}"
        
        print(f"📤 Отправка ответа в Telegram (длина: {len(response)} символов)...")
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
        print("✅ Ответ успешно отправлен!")
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд info.py...")
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!кто админ\b'), cmd_who_admin))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!инфа\b'), cmd_info))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!info\b'), cmd_info))
    print("✅ info.py зарегистрирован")