"""
ТЕСТОВАЯ КОМАНДА
"""
from telegram.ext import MessageHandler, filters

async def cmd_test(update, context):
    """Обработчик команды !тест"""
    print("✅ КОМАНДА !тест ВЫПОЛНЕНА!")
    await update.message.reply_text("✅ Команда работает!")

def register(app):
    """Регистрация команды"""
    print("  📝 Регистрация команды !тест")
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^!тест\b'), 
        cmd_test
    ))