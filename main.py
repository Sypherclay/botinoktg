#!/usr/bin/env python3
"""
ГЛАВНЫЙ ФАЙЛ БОТА - МИНИМАЛЬНАЯ ВЕРСИЯ
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

# Простой дебаггер
async def debug_all(update, context):
    if update.message:
        print(f"\n📨 СООБЩЕНИЕ: {update.message.text}")
        print(f"   Это команда? {update.message.text and update.message.text.startswith(('!', '/'))}")

# Простая тестовая команда прямо здесь
async def test_direct(update, context):
    print("🔥🔥🔥 ПРЯМАЯ КОМАНДА СРАБОТАЛА! 🔥🔥🔥")
    await update.message.reply_text("✅ Прямая команда работает!")

def main():
    print("\n" + "="*50)
    print("🚀 МИНИМАЛЬНЫЙ ТЕСТ")
    print("="*50)
    
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    setup_logger('bot')
    init_database()
    set_owner_id(OWNER_ID)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # 1. ПРЯМАЯ ТЕСТОВАЯ КОМАНДА (самый высокий приоритет)
    print("➕ Добавление прямой тестовой команды")
    app.add_handler(CommandHandler("testdirect", test_direct))
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^!прямая\b'), 
        test_direct
    ))
    
    # 2. Дебаггер (видит всё)
    app.add_handler(MessageHandler(filters.ALL, debug_all), group=-1)
    
    # 3. Все команды из папки
    print("\n📦 Загрузка команд из папки...")
    register_all_commands(app)
    
    # 4. Callback обработчик
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    print("\n" + "="*50)
    print("✅ БОТ ГОТОВ!")
    print("="*50 + "\n")
    
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")