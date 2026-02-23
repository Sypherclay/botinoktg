"""
ОБРАБОТЧИК КНОПОК
Все callback запросы от inline клавиатур
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import is_moderator_db
from permissions import is_admin, is_owner

# Хранилище сессий (общее с commands/stats.py)
# Используем тот же словарь, что и в stats.py
from commands.stats import user_selections as stats_selections

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик всех callback кнопок"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # ========== СТАТИСТИКА (доступно модераторам) ==========
    if data.startswith(("stats_", "quick_")):
        if not (is_admin(user_id) or is_owner(user_id) or is_moderator_db(user_id)):
            await query.edit_message_text("❌ Доступ запрещен")
            return
        
        # Передаём в stats обработчик
        from commands.stats import stats_callback
        await stats_callback(update, context)
        return
    
    # ========== АДМИНСКИЕ КНОПКИ ==========
    if not is_admin(user_id):
        await query.edit_message_text("❌ Доступ запрещен")
        return
    
    # Отмена
    if data == "cancel":
        await query.edit_message_text("❌ Операция отменена")
        if user_id in stats_selections:
            del stats_selections[user_id]
        return
    
    # Добавление чата
    if data == "add_chat_manual":
        await query.edit_message_text(
            "📝 Введите ID чата:\n/addchat -1001234567890"
        )
        return
    
    # Если кнопка не обработана
    await query.edit_message_text(f"ℹ️ Неизвестный запрос: {data}")