"""
ТОП-КОМАНДЫ
!топ баланс, !топ наказания, !топ актив
"""
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
import sqlite3
from database import DB_PATH
from permissions import get_clickable_name

async def cmd_top(update, context):
    """!топ [баланс/наказания/актив]"""
    chat_id = str(update.effective_chat.id)
    
    if not context.args:
        await update.message.reply_text(
            "❌ Используйте:\n"
            "• !топ баланс\n"
            "• !топ наказания\n"
            "• !топ актив",
            parse_mode=ParseMode.HTML
        )
        return
    
    sub = context.args[0].lower()
    
    if sub == 'баланс':
        await top_balance(update, chat_id)
    elif sub == 'наказания':
        await top_punishments(update, chat_id)
    elif sub == 'актив':
        await top_activity(update, chat_id)
    else:
        await update.message.reply_text(f"❌ Неизвестно: {sub}")

async def top_balance(update, chat_id):
    """Топ по балансу"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.user_id, u.name, u.username, s.balance
        FROM users u
        JOIN salary s ON u.user_id = s.user_id
        WHERE u.chat_id = ? AND s.balance > 0
        ORDER BY s.balance DESC
        LIMIT 10
    ''', (chat_id,))
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("📭 Нет пользователей с балансом")
        return
    
    lines = ["💰 <b>ТОП ПО БАЛАНСУ</b>", ""]
    medals = ['🥇', '🥈', '🥉']
    
    for i, (uid, name, username, bal) in enumerate(users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        clickable = get_clickable_name(uid, name or f"User {uid}", username or "")
        lines.append(f"{medal} {clickable} — {bal} HC")
    
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def top_punishments(update, chat_id):
    """Топ по наказаниям"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, name, username, punishments
        FROM users
        WHERE chat_id = ? AND punishments > 0
        ORDER BY punishments DESC
        LIMIT 10
    ''', (chat_id,))
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("📭 Нет пользователей с наказаниями")
        return
    
    lines = ["⚠️ <b>ТОП ПО НАКАЗАНИЯМ</b>", ""]
    medals = ['🥇', '🥈', '🥉']
    
    for i, (uid, name, username, pun) in enumerate(users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        clickable = get_clickable_name(uid, name or f"User {uid}", username or "")
        lines.append(f"{medal} {clickable} — {pun} наказаний")
    
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def top_activity(update, chat_id):
    """Топ по активности"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, name, username, count
        FROM users
        WHERE chat_id = ? AND count > 0
        ORDER BY count DESC
        LIMIT 10
    ''', (chat_id,))
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("📭 Нет активных пользователей")
        return
    
    lines = ["💬 <b>ТОП ПО АКТИВНОСТИ</b>", ""]
    medals = ['🥇', '🥈', '🥉']
    
    for i, (uid, name, username, cnt) in enumerate(users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        clickable = get_clickable_name(uid, name or f"User {uid}", username or "")
        lines.append(f"{medal} {clickable} — {cnt} сообщений")
    
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

def register(app):
    app.add_handler(CommandHandler("топ", cmd_top))