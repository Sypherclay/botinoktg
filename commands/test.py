"""
ТЕСТОВАЯ КОМАНДА
"""
from telegram.ext import MessageHandler, filters

async def cmd_test(update, context):
    """Обработчик команды !тест"""
    print("🔥🔥🔥 КОМАНДА ИЗ ФАЙЛА test.py СРАБОТАЛА! 🔥🔥🔥")
    print(f"   Пользователь: {update.effective_user.first_name}")
    print(f"   Чат: {update.effective_chat.id}")
    await update.message.reply_text("✅ Команда из файла test.py работает!")

def register(app):
    """Регистрация команды"""
    print("  📝 Регистрация команды !тест в test.py")
    # Добавляем обработчик для !тест
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^!тест\b'), 
        cmd_test
    ))
    # Добавляем для /тест
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^/тест\b'), 
        cmd_test
    ))