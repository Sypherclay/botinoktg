"""
СИСТЕМА ЗАРПЛАТ
!зп, !плюс, !минус, -зп, /addzarplata, /removezarplata, /zptest
"""
from datetime import datetime, timedelta
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
import sqlite3
from database import (
    get_salary_counter, add_to_salary_counter, reset_salary_counter,
    get_user_balance, add_to_balance, subtract_from_balance,
    get_user_info, get_user_rank_db, get_setting, set_setting,
    get_all_users_in_chat, add_payout_history, get_payout_settings,
    save_payout_settings, get_user_by_username, get_user_id_by_custom_nick,
    DB_PATH
)
from permissions import is_admin, is_owner, get_user_rank, get_clickable_name
from user_resolver import resolve_user
from constants import RANKS, ANONYMOUS_ADMIN_ID, OWNER_ID
from logger import log_admin_action, log_command

# ========== КОМАНДЫ УПРАВЛЕНИЯ ТЕМОЙ ==========

async def cmd_addzarplata(update, context):
    """Установить тему для выплат /addzarplata ID_темы"""
    user_id = update.effective_user.id
    
    if not (is_admin(user_id) or is_owner(user_id)):
        await update.message.reply_text("❌ Только администраторы могут использовать эту команду")
        return
    
    settings = get_payout_settings()
    
    if not context.args:
        current = settings.get('payout_topic_id')
        if current:
            await update.message.reply_text(
                f"ℹ️ Текущая тема: <code>{current}</code>\n"
                f"/addzarplata ID_темы",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text("/addzarplata ID_темы")
        return
    
    topic_id = context.args[0]
    
    try:
        int(topic_id)
        now = datetime.now()
        settings['payout_topic_id'] = topic_id
        settings['topic_set_date'] = now.isoformat()
        settings['last_payout'] = None
        settings['next_payout'] = (now + timedelta(days=30)).isoformat()
        save_payout_settings(settings)
        
        first_date = (now + timedelta(days=30)).strftime("%d.%m.%Y")
        
        await update.message.reply_text(
            f"✅ Тема установлена: <code>{topic_id}</code>\n"
            f"📅 Первая выплата: {first_date}",
            parse_mode=ParseMode.HTML
        )
    except ValueError:
        await update.message.reply_text("❌ ID темы должен быть числом")

async def cmd_removezarplata(update, context):
    """Удалить тему для выплат /removezarplata"""
    user_id = update.effective_user.id
    
    if not (is_admin(user_id) or is_owner(user_id)):
        await update.message.reply_text("❌ Только администраторы")
        return
    
    settings = get_payout_settings()
    current = settings.get('payout_topic_id')
    
    settings['payout_topic_id'] = None
    settings['topic_set_date'] = None
    settings['last_payout'] = None
    settings['next_payout'] = None
    save_payout_settings(settings)
    
    if current:
        await update.message.reply_text(f"✅ Тема удалена: <code>{current}</code>", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("ℹ️ Тема не была установлена")

# ========== КОМАНДА !ЗП ==========

async def cmd_zp(update, context):
    """!зп - показать заработок пользователей"""
    chat_id = str(update.effective_chat.id)
    
    users = []
    for uid, name, username in get_all_users_in_chat(chat_id):
        counter = get_salary_counter(uid)
        balance = get_user_balance(uid)
        if counter > 0 or balance > 0:
            clickable = get_clickable_name(uid, name, username)
            users.append({
                'name': clickable,
                'counter': counter,
                'balance': balance,
                'uid': uid
            })
    
    if not users:
        await update.message.reply_text("📭 Нет пользователей с данными о зарплатах")
        return
    
    users.sort(key=lambda x: x['balance'], reverse=True)
    
    lines = ["💰 <b>Заработок пользователей</b>", ""]
    for u in users:
        lines.append(f"👤 {u['name']}")
        lines.append(f"   💰 Накоплено к выплате: {u['counter']}")
        lines.append(f"   💵 Баланс: {u['balance']} HC")
        lines.append("")
    
    lines.append(f"👥 Всего: {len(users)} пользователей")
    
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

# ========== КОМАНДЫ БАЛАНСА ==========

async def cmd_plus(update, context):
    """!плюс число (ответом) - начислить коины"""
    user_id = update.effective_user.id
    
    if not (is_admin(user_id) or is_owner(user_id)):
        await update.message.reply_text("❌ Только администраторы")
        return
    
    if not context.args:
        await update.message.reply_text("!плюс число (ответом)")
        return
    
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Число должно быть положительным")
            return
    except ValueError:
        await update.message.reply_text("❌ Укажите число")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение пользователя")
        return
    
    target = update.message.reply_to_message.from_user
    new = add_to_balance(target.id, amount)
    clickable = get_clickable_name(target.id, target.first_name, target.username)
    
    await update.message.reply_text(
        f"✅ Начислено {amount} HC {clickable}\n💰 Баланс: {new}",
        parse_mode=ParseMode.HTML
    )

async def cmd_minus(update, context):
    """!минус число (ответом) - списать коины"""
    user_id = update.effective_user.id
    
    if not (is_admin(user_id) or is_owner(user_id)):
        await update.message.reply_text("❌ Только администраторы")
        return
    
    if not context.args:
        await update.message.reply_text("!минус число (ответом)")
        return
    
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Число должно быть положительным")
            return
    except ValueError:
        await update.message.reply_text("❌ Укажите число")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение пользователя")
        return
    
    target = update.message.reply_to_message.from_user
    success, new = subtract_from_balance(target.id, amount)
    clickable = get_clickable_name(target.id, target.first_name, target.username)
    
    if success:
        await update.message.reply_text(
            f"✅ Списано {amount} HC у {clickable}\n💰 Баланс: {new}",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            f"❌ У {clickable} недостаточно средств\n💰 Баланс: {new}",
            parse_mode=ParseMode.HTML
        )

# ========== КОМАНДА + (БЫСТРОЕ НАЧИСЛЕНИЕ) ==========

async def cmd_plus_reply(update, context):
    """Команда '+' - +1 к счётчику (только ответом)"""
    user_id = update.effective_user.id
    
    if not (is_admin(user_id) or get_user_rank(user_id) == 'curator'):
        await update.message.reply_text("❌ Только админы и кураторы")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Эта команда работает только как ответ на сообщение")
        return
    
    target = update.message.reply_to_message.from_user
    
    if target.id == user_id:
        await update.message.reply_text("❌ Нельзя начислять себе")
        return
    
    if target.is_bot:
        await update.message.reply_text("❌ Нельзя начислять боту")
        return
    
    new = add_to_salary_counter(target.id, 1)
    balance = get_user_balance(target.id)
    clickable = get_clickable_name(target.id, target.first_name, target.username)
    
    await update.message.reply_text(
        f"✅ Счётчик для {clickable} +1\n📊 Текущий: {new}\n💰 Баланс: {balance} HC",
        parse_mode=ParseMode.HTML
    )

# ========== КОМАНДА -ЗП (УДАЛЕНИЕ ИЗ СИСТЕМЫ) ==========

async def cmd_remove_from_salary(update, context):
    """-зп - удалить пользователя из системы зарплат"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not (is_admin(user_id) or get_user_rank(user_id) == 'curator'):
        await update.message.reply_text("❌ Только админы и кураторы")
        return
    
    user = await resolve_user(update, context)
    if not user:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT salary_counter, balance FROM salary WHERE user_id = ?', (user.id,))
    data = cursor.fetchone()
    counter = data[0] if data else 0
    balance = data[1] if data else 0
    
    cursor.execute('SELECT punishments FROM users WHERE user_id = ? AND chat_id = ?', (user.id, chat_id))
    pun = cursor.fetchone()
    punishments = pun[0] if pun else 0
    
    cursor.execute('DELETE FROM salary WHERE user_id = ?', (user.id,))
    conn.commit()
    conn.close()
    
    clickable = get_clickable_name(user.id, user.first_name, user.username)
    
    await update.message.reply_text(
        f"✅ {clickable} удалён из системы зарплат!\n\n"
        f"📊 Было:\n"
        f"   • Счётчик: {counter}\n"
        f"   • Баланс: {balance} HC\n"
        f"   • Наказаний: {punishments}",
        parse_mode=ParseMode.HTML
    )

# ========== ТЕСТОВАЯ КОМАНДА ==========

async def cmd_zptest(update, context):
    """Тестовый расчёт зарплат"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Только администраторы")
        return
    
    settings = get_payout_settings()
    topic = settings.get('payout_topic_id')
    
    if not topic:
        await update.message.reply_text("❌ Тема не настроена. /addzarplata ID_темы")
        return
    
    rate = int(settings.get('rate_per_punishment', 10))
    
    users = []
    total = 0
    
    for uid, name, username in get_all_users_in_chat(chat_id):
        count = get_salary_counter(uid)
        if count > 0:
            salary = count * rate
            rank = get_user_rank_db(uid)
            rank_name = RANKS.get(rank, {}).get('name', 'Участник')
            clickable = get_clickable_name(uid, name, username)
            users.append({
                'rank': rank,
                'rank_name': rank_name,
                'name': clickable,
                'count': count,
                'salary': salary
            })
            total += salary
    
    users.sort(key=lambda x: x['salary'], reverse=True)
    
    lines = ["🧪 <b>ТЕСТОВЫЙ РАСЧЁТ</b>", "="*35]
    
    topic_set = settings.get('topic_set_date')
    if topic_set:
        d = datetime.fromisoformat(topic_set)
        lines.append(f"📅 Тема установлена: {d.strftime('%d.%m.%Y')}")
    
    lines.append(f"💎 Курс: {rate} HC")
    lines.append("="*35 + "\n")
    
    for u in users:
        lines.append(f"🎖️ <b>{u['rank_name']}</b> {u['name']}")
        lines.append(f"   📊 Накоплено: {u['count']}")
        lines.append(f"   💰 Получит: {u['salary']} HC\n")
    
    lines.append("="*35)
    lines.append(f"📊 Всего к выплате: {total} HC")
    lines.append(f"👥 Получат: {len(users)} человек")
    lines.append("="*35)
    lines.append("🔄 <i>Это тест. Счётчики не сбрасываются</i>")
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=int(topic),
        text="\n".join(lines),
        parse_mode=ParseMode.HTML
    )
    
    await update.message.reply_text("✅ Тест отправлен в тему")

def register(app):
    app.add_handler(CommandHandler("addzarplata", cmd_addzarplata))
    app.add_handler(CommandHandler("removezarplata", cmd_removezarplata))
    app.add_handler(CommandHandler("zptest", cmd_zptest))
    app.add_handler(MessageHandler("зп", cmd_zp))
    app.add_handler(MessageHandler("плюс", cmd_plus))
    app.add_handler(MessageHandler("минус", cmd_minus))
    app.add_handler(MessageHandler("зп", cmd_zp))
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^-зп\b'),
        cmd_remove_from_salary
    ))
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^\+$'),
        cmd_plus_reply
    ))