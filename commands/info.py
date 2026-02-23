"""
info.py - МАКСИМАЛЬНО ПРОСТАЯ ТЕСТОВАЯ ВЕРСИЯ
"""
from telegram.ext import MessageHandler, filters

print("✅ ТЕСТОВЫЙ info.py загружен!")

async def cmd_info(update, context):
    """Максимально простая тестовая команда"""
    print("🔥🔥🔥 ТЕСТОВАЯ КОМАНДА !инфа СРАБОТАЛА! 🔥🔥🔥")
    print(f"   Текст: {update.message.text}")
    print(f"   От: {update.effective_user.first_name}")
    await update.message.reply_text("✅ ТЕСТОВАЯ КОМАНДА РАБОТАЕТ!")

async def cmd_who_admin(update, context):
    """Максимально простая тестовая команда"""
    print("🔥🔥🔥 ТЕСТОВАЯ КОМАНДА !кто админ СРАБОТАЛА! 🔥🔥🔥")
    await update.message.reply_text("✅ ТЕСТОВАЯ КОМАНДА !кто админ РАБОТАЕТ!")

def register(app):
    print("📝 Регистрация тестовых команд info.py...")
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!кто админ\b'), cmd_who_admin))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!инфа\b'), cmd_info))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!info\b'), cmd_info))
    print("✅ Тестовый info.py зарегистрирован")