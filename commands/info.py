"""
ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЯХ
!инфа, !кто админ
"""
from datetime import datetime
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from database import (
    get_user_info, get_user_custom_nick, get_user_rank_db,
    get_user_warnings_count, get_user_max_warnings,
    get_vacation_info, get_user_balance, get_setting,
    get_user_by_username, get_user_id_by_custom_nick, get_user_rewards
)
from permissions import has_permission, get_clickable_name
from user_resolver import resolve_user
from constants import RANKS, OWNER_ID
import sqlite3
from database import DB_PATH

async def cmd_who_admin(update, context):
    """!кто админ - список администраторов по рангам"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not has_permission(user_id, '!кто админ'):
        await update.message.reply_text("❌ Нет прав")
        return
    
    # Группируем по рангам
    owners, curators, deputies, managers, moders, customs, helpers = [], [], [], [], [], [], []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, rank FROM ranks')
    ranks = cursor.fetchall()
    conn.close()
    
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

async def cmd_info(update, context):
    """!инфа - информация о пользователе"""
    chat_id = str(update.effective_chat.id)
    
    # Поиск пользователя
    user = await resolve_user(update, context, required=False, allow_self=True)
    if not user:
        return
    
    # Получаем данные
    info = get_user_info(user.id, chat_id)
    name = info[0] if info else user.first_name
    username = info[1] if info else user.username
    
    custom = get_user_custom_nick(user.id)
    display = custom if custom else name
    
    clickable = get_clickable_name(user.id, display, username)
    
    rank = get_user_rank_db(user.id)
    rank_name = RANKS.get(rank, {}).get('name', 'Участник')
    
    warnings = get_user_warnings_count(user.id, chat_id)
    max_w = int(get_setting('max_warnings', '3'))
    
    immunity = rank in ['owner', 'curator', 'custom', 'helper_plus']
    
    vacation = get_vacation_info(user.id)
    used_days = vacation[2] if vacation else 0
    limit = int(get_setting('max_vacation_days', '14'))
    
    if vacation and datetime.now() <= datetime.fromisoformat(vacation[1]):
        vacation_status = f"до {datetime.fromisoformat(vacation[1]).strftime('%d.%m.%Y')}"
    else:
        vacation_status = "нет"
    
    balance = get_user_balance(user.id)
    
    # Топ-позиции
    top_activity = get_top_user(chat_id, 'count')
    top_punish = get_top_user(chat_id, 'punishments')
    top_balance = get_top_balance(chat_id)
    
    badges = []
    if user.id == top_activity:
        badges.append("🏆 ТОП-1 Актив")
    if user.id == top_punish:
        badges.append("👑 ТОП-1 Наказания")
    if user.id == top_balance:
        badges.append("💎 ТОП-1 Баланс")
    
    # Награды
    rewards = get_user_rewards(user.id)
    reward_badges = ['💸 ЗА ДЕНЬГИ ДА' if '10_complaints' in rewards else '']
    reward_badges = [r for r in reward_badges if r]
    
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
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

# Вспомогательные функции для топов
def get_top_user(chat_id, field):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'SELECT user_id FROM users WHERE chat_id = ? ORDER BY {field} DESC LIMIT 1', (chat_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def get_top_balance(chat_id):
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

def register(app):
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^!кто админ\b'),
        cmd_who_admin
    ))
    app.add_handler(CommandHandler("инфа", cmd_info))
    app.add_handler(CommandHandler("info", cmd_info))