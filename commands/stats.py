"""
СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ
/stats, /quickstats, меню статистики
"""
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from database import (
    get_all_chats, get_chat_topics, get_topic_users,
    get_user_info, get_user_custom_nick, get_user_punishments,
    get_user_warnings_count, get_user_max_warnings, get_user_topic_count
)
from permissions import is_admin, is_owner
from database import is_moderator_db
from logger import log_command

# Хранилище сессий (в памяти)
user_selections = {}

async def cmd_stats(update, context):
    """Главное меню статистики"""
    user_id = update.effective_user.id
    
    # Проверка доступа
    if not (is_admin(user_id) or is_owner(user_id) or is_moderator_db(user_id)):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    # Инициализация сессии
    user_selections[user_id] = {
        'chat_id': None,
        'topic_id': None,
        'user_id': None,
        'step': 'select_chat'
    }
    
    # Получаем все чаты
    chats = get_all_chats()
    
    keyboard = []
    for chat_id in chats:
        # Пытаемся получить название
        try:
            chat = await context.bot.get_chat(int(chat_id))
            name = chat.title or chat_id
        except:
            name = chat_id
        
        keyboard.append([InlineKeyboardButton(
            f"💬 {name[:30]}",
            callback_data=f"stats_chat_{chat_id}"
        )])
    
    if not chats:
        keyboard.append([InlineKeyboardButton("📭 Нет чатов", callback_data="stats_nochats")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="stats_cancel")])
    
    await update.message.reply_text(
        "📊 <b>Статистика</b>\n\nВыберите чат:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def cmd_quickstats(update, context):
    """Быстрая статистика"""
    user_id = update.effective_user.id
    
    if not (is_admin(user_id) or is_owner(user_id) or is_moderator_db(user_id)):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    user_selections[user_id] = {'chat_id': None, 'topic_id': '0'}
    
    chats = get_all_chats()
    keyboard = []
    
    for chat_id in chats:
        keyboard.append([InlineKeyboardButton(f"📊 {chat_id}", callback_data=f"quick_chat_{chat_id}")])
    
    if not chats:
        keyboard.append([InlineKeyboardButton("📭 Нет чатов", callback_data="stats_nochats")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="stats_cancel")])
    
    await update.message.reply_text(
        "📊 <b>Быстрая статистика</b>\n\nВыберите чат:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def stats_callback(update, context):
    """Обработчик кнопок статистики"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Проверка доступа
    if not (is_admin(user_id) or is_owner(user_id) or is_moderator_db(user_id)):
        await query.edit_message_text("❌ Доступ запрещен")
        return
    
    # Отмена
    if data == "stats_cancel":
        if user_id in user_selections:
            del user_selections[user_id]
        await query.edit_message_text("❌ Отменено")
        return
    
    if data == "stats_nochats":
        await query.edit_message_text("📭 Нет доступных чатов")
        return
    
    # Выбор чата
    if data.startswith("stats_chat_"):
        chat_id = data.replace("stats_chat_", "")
        user_selections[user_id]['chat_id'] = chat_id
        user_selections[user_id]['step'] = 'select_topic'
        
        await show_topics(query, chat_id)
        return
    
    if data.startswith("quick_chat_"):
        chat_id = data.replace("quick_chat_", "")
        user_selections[user_id]['chat_id'] = chat_id
        await show_quick_stats(query, chat_id)
        return
    
    # Выбор темы
    if data.startswith("stats_topic_"):
        topic = data.replace("stats_topic_", "")
        if topic == "all":
            user_selections[user_id]['topic_id'] = None
        else:
            user_selections[user_id]['topic_id'] = topic
        
        await show_users(query, user_id)
        return
    
    # Назад
    if data == "stats_back_chat":
        del user_selections[user_id]
        await cmd_stats(update, context)
        return
    
    if data == "stats_back_topic":
        user_selections[user_id]['step'] = 'select_topic'
        await show_topics(query, user_selections[user_id]['chat_id'])
        return
    
    if data == "stats_back_user":
        await show_users(query, user_id)
        return
    
    # Выбор пользователя
    if data.startswith("stats_user_"):
        uid = data.replace("stats_user_", "")
        if uid == "all":
            await show_all_stats(query, user_id)
        else:
            await show_user_stats(query, user_id, int(uid))
        return

async def show_topics(query, chat_id):
    """Показать выбор темы"""
    keyboard = [
        [InlineKeyboardButton("📌 Все темы", callback_data="stats_topic_all")],
        [InlineKeyboardButton("📌 Без темы (0)", callback_data="stats_topic_0")]
    ]
    
    topics = get_chat_topics(chat_id)
    for tid, name, count in topics:
        if tid != '0':
            keyboard.append([InlineKeyboardButton(
                f"📌 {name[:20]} ({count})",
                callback_data=f"stats_topic_{tid}"
            )])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="stats_back_chat")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="stats_cancel")])
    
    await query.edit_message_text(
        f"💬 Чат: <code>{chat_id}</code>\n\nВыберите тему:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_users(query, user_id):
    """Показать выбор пользователя"""
    sel = user_selections[user_id]
    chat_id = sel['chat_id']
    topic = sel['topic_id']
    
    users = get_topic_users(chat_id, topic)
    
    if not users:
        await query.edit_message_text("📭 Нет пользователей")
        return
    
    keyboard = [[InlineKeyboardButton("👥 Все пользователи", callback_data="stats_user_all")]]
    keyboard.append([InlineKeyboardButton("────── Топ ──────", callback_data="stats_nop")])
    
    for uid, name, username, count in users[:20]:
        nick = get_user_custom_nick(uid)
        display = (nick or name or f"User {uid}")[:20]
        keyboard.append([InlineKeyboardButton(
            f"👤 {display} ({count})",
            callback_data=f"stats_user_{uid}"
        )])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад к темам", callback_data="stats_back_topic")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="stats_cancel")])
    
    topic_text = "Все темы" if topic is None else f"Тема {topic}"
    await query.edit_message_text(
        f"💬 Чат: <code>{chat_id}</code>\n📌 {topic_text}\n\nВыберите пользователя:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_user_stats(query, user_id, target_id):
    """Статистика одного пользователя"""
    sel = user_selections[user_id]
    chat_id = sel['chat_id']
    topic = sel['topic_id']
    
    info = get_user_info(target_id, chat_id)
    name = info[0] if info else f"User {target_id}"
    username = info[1] if info else ""
    
    nick = get_user_custom_nick(target_id)
    display = nick if nick else name
    
    from permissions import get_clickable_name
    clickable = get_clickable_name(target_id, display, username)
    
    total = get_user_topic_count(chat_id, topic, target_id)
    punish = get_user_punishments(target_id, chat_id)
    warns = get_user_warnings_count(target_id, chat_id)
    max_w = get_user_max_warnings(target_id)
    
    topic_text = "Все темы" if topic is None else f"Тема {topic}"
    
    text = f"📊 <b>Статистика</b>\n\n"
    text += f"👤 {clickable}\n"
    text += f"🆔 <code>{target_id}</code>\n"
    text += f"💬 Чат: <code>{chat_id}</code>\n"
    text += f"📌 Тема: {topic_text}\n\n"
    text += f"📨 Сообщений: {total}\n"
    text += f"⚖️ Наказания: {punish}\n"
    text += f"⚠️ Выговоров: {warns}/{max_w}\n"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="stats_back_user")],
        [InlineKeyboardButton("🔄 Новый запрос", callback_data="stats_new")],
        [InlineKeyboardButton("❌ Отмена", callback_data="stats_cancel")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_all_stats(query, user_id):
    """Статистика всех пользователей"""
    sel = user_selections[user_id]
    chat_id = sel['chat_id']
    topic = sel['topic_id']
    
    users = get_topic_users(chat_id, topic)
    total = sum(c for _, _, _, c in users)
    
    topic_text = "Все темы" if topic is None else f"Тема {topic}"
    
    text = f"📊 <b>Статистика всех</b>\n\n"
    text += f"💬 Чат: <code>{chat_id}</code>\n"
    text += f"📌 {topic_text}\n"
    text += f"👥 Уникальных: {len(users)}\n"
    text += f"📨 Всего сообщений: {total}\n\n"
    text += "<b>Топ:</b>\n"
    
    for i, (uid, name, username, count) in enumerate(users[:20], 1):
        nick = get_user_custom_nick(uid)
        display = nick or name or f"User {uid}"
        pct = (count / total * 100) if total > 0 else 0
        text += f"{i}. {display}: {count} ({pct:.1f}%)\n"
    
    if len(users) > 20:
        text += f"\n... и ещё {len(users) - 20}"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="stats_back_user")],
        [InlineKeyboardButton("🔄 Новый запрос", callback_data="stats_new")],
        [InlineKeyboardButton("❌ Отмена", callback_data="stats_cancel")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_quick_stats(query, chat_id):
    """Быстрая статистика по чату"""
    users = get_topic_users(chat_id, None)
    total = sum(c for _, _, _, c in users)
    
    text = f"📊 <b>Быстрая статистика</b>\n\n"
    text += f"💬 Чат: <code>{chat_id}</code>\n"
    text += f"👥 Пользователей: {len(users)}\n"
    text += f"📨 Сообщений: {total}\n\n"
    text += "<b>Топ-10:</b>\n"
    
    for i, (uid, name, username, count) in enumerate(users[:10], 1):
        nick = get_user_custom_nick(uid)
        display = nick or name or f"User {uid}"
        pct = (count / total * 100) if total > 0 else 0
        text += f"{i}. {display}: {count} ({pct:.1f}%)\n"
    
    keyboard = [[InlineKeyboardButton("🔄 Новый запрос", callback_data="stats_new")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

def register(app):
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("quickstats", cmd_quickstats))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats_"))