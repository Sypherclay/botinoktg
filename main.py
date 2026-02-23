#!/usr/bin/env python3
"""
ГЛАВНЫЙ ФАЙЛ - МИНИМАЛЬНАЯ ВЕРСИЯ ДЛЯ ТЕСТА
"""
import os
from telegram.ext import Application, MessageHandler, filters
from config import BOT_TOKEN
from commands import register_all_commands
from database import init_database
from logger import setup_logger
from user_resolver import set_owner_id
from config import OWNER_ID

async def debug_all(update, context):
    """Дебаггер"""
    if update.message:
        print(f"\n📨 СООБЩЕНИЕ: {update.message.text}")
        print(f"   Это команда? {update.message.text and update.message.text.startswith('!')}")

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
    
    # 1. СНАЧАЛА команды
    print("\n📦 Загрузка команд...")
    register_all_commands(app)
    
    # 2. ПОТОМ дебаггер (самый низкий приоритет)
    print("\n🔍 Регистрация дебаггера...")
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