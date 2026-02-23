#!/usr/bin/env python3
"""
ГЛАВНЫЙ ФАЙЛ - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import os
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from config import BOT_TOKEN
from commands import register_all_commands
from keyboards.callback_handler import handle_callback_query
from database import init_database
from logger import setup_logger
from user_resolver import set_owner_id
from config import OWNER_ID

# Прямые тестовые команды
async def test_direct(update, context):
    print("🔥🔥🔥 ПРЯМАЯ КОМАНДА СРАБОТАЛА!")
    await update.message.reply_text("✅ Прямая команда работает!")

# Дебаггер - будет ПОСЛЕДНИМ
async def debug_all(update, context):
    if update.message and update.message.text:
        print(f"\n📨 СООБЩЕНИЕ: {update.message.text}")
        print(f"   Это команда? {update.message.text and update.message.text.startswith(('!', '/'))}")

def main():
    print("\n" + "="*50)
    print("🚀 ИСПРАВЛЕННАЯ ВЕРСИЯ")
    print("="*50)
    
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    setup_logger('bot')
    init_database()
    set_owner_id(OWNER_ID)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ===== ВАЖНО: ПРАВИЛЬНЫЙ ПОРЯДОК =====
    
    # 1. СНАЧАЛА прямые команды
    print("\n➕ 1. Регистрация прямых команд...")
    app.add_handler(CommandHandler("testdirect", test_direct))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!прямая\b'), test_direct))
    
    # 2. ПОТОМ все команды из папки commands/
    print("\n📦 2. Загрузка команд из папки commands/...")
    register_all_commands(app)
    
    # 3. ПОТОМ callback обработчик
    print("\n🔘 3. Регистрация callback обработчика...")
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # 4. ДЕБАГГЕР - В САМОМ КОНЦЕ (group=-1 означает самый низкий приоритет)
    print("\n🔍 4. Регистрация дебаггера...")
    app.add_handler(MessageHandler(filters.ALL, debug_all), group=-1)
    
    print("\n" + "="*50)
    print("✅ БОТ ГОТОВ!")
    print("="*50 + "\n")
    
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")