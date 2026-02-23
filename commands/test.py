"""
ТЕСТОВАЯ КОМАНДА - МАКСИМАЛЬНО ПРОСТАЯ
"""
from telegram.ext import MessageHandler, filters

async def cmd_test(update, context):
    """Самая простая тестовая команда"""
    print("🔥🔥🔥🔥🔥 ТЕСТОВАЯ КОМАНДА СРАБОТАЛА! 🔥🔥🔥🔥🔥")
    print(f"   Текст: {update.message.text}")
    print(f"   От: {update.effective_user.id}")
    await update.message.reply_text("✅ РАБОТАЕТ!")

def register(app):
    """Регистрация"""
    print("  📝 РЕГИСТРАЦИЯ ТЕСТОВОЙ КОМАНДЫ")
    # Только одна команда для простоты
    app.add_handler(MessageHandler(
        filters.Regex(r'^!тест$'),  # Точное совпадение, без пробелов
        cmd_test
    ))