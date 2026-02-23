"""
ТОП-КОМАНДЫ
!топ баланс, !топ наказания, !топ актив
"""
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
import sqlite3
import traceback
from database import DB_PATH
from permissions import get_clickable_name

print("✅ top.py загруден!")

async def cmd_top(update, context):
    """!топ [баланс/наказания/актив]"""
    print("\n🔥 ВЫПОЛНЕНИЕ !топ")
    
    try:
        chat_id = str(update.effective_chat.id)
        print(f"   chat_id: {chat_id}")
        
        # ✅ Получаем текст сообщения и разбиваем на части
        message_text = update.message.text
        print(f"   текст: {message_text}")
        
        parts = message_text.split()
        print(f"   части: {parts}")
        
        # Если есть только команда без аргументов
        if len(parts) == 1:
            await update.message.reply_text(
                "❌ Используйте:\n"
                "• !топ баланс\n"
                "• !топ наказания\n"
                "• !топ актив",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Получаем подкоманду (второе слово)
        sub = parts[1].lower()
        print(f"   подкоманда: {sub}")
        
        if sub == 'баланс':
            await top_balance(update, chat_id)
        elif sub == 'наказания':
            await top_punishments(update, chat_id)
        elif sub == 'актив':
            await top_activity(update, chat_id)
        else:
            await update.message.reply_text(
                f"❌ Неизвестная подкоманда: {sub}\n"
                f"Используйте: баланс, наказания, актив"
            )
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_top: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def top_balance(update, chat_id):
    """Топ по балансу"""
    print("   📊 Топ по балансу")
    
    try:
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
            display_name = name or f"User {uid}"
            clickable = get_clickable_name(uid, display_name, username or "")
            lines.append(f"{medal} {clickable} — {bal} HC")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        print("   ✅ Топ баланса отправлен")
        
    except Exception as e:
        print(f"   ❌ Ошибка в top_balance: {e}")
        raise

async def top_punishments(update, chat_id):
    """Топ по наказаниям"""
    print("   📊 Топ по наказаниям")
    
    try:
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
            display_name = name or f"User {uid}"
            clickable = get_clickable_name(uid, display_name, username or "")
            lines.append(f"{medal} {clickable} — {pun} наказаний")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        print("   ✅ Топ наказаний отправлен")
        
    except Exception as e:
        print(f"   ❌ Ошибка в top_punishments: {e}")
        raise

async def top_activity(update, chat_id):
    """Топ по активности"""
    print("   📊 Топ по активности")
    
    try:
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
            display_name = name or f"User {uid}"
            clickable = get_clickable_name(uid, display_name, username or "")
            lines.append(f"{medal} {clickable} — {cnt} сообщений")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        print("   ✅ Топ активности отправлен")
        
    except Exception as e:
        print(f"   ❌ Ошибка в top_activity: {e}")
        raise

def register(app):
    print("📝 Регистрация команд top.py...")
    # Регистрируем на все команды, начинающиеся с !топ
    app.add_handler(MessageHandler(filters.Regex(r'^!топ\b'), cmd_top))
    print("✅ top.py зарегистрирован")