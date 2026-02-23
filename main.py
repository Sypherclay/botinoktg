#!/usr/bin/env python3
"""
ГЛАВНЫЙ ФАЙЛ БОТА - ДИАГНОСТИЧЕСКАЯ ВЕРСИЯ
"""
import logging
import os
import sys
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from config import BOT_TOKEN
from commands import register_all_commands
from handlers.message_handler import handle_message
from keyboards.callback_handler import handle_callback_query
from database import init_database
from logger import setup_logger, log_bot_event
from user_resolver import set_owner_id
from config import OWNER_ID

# Простейшая команда для теста
async def test_command(update, context):
    """Тестовая команда /test"""
    print("✅ ТЕСТОВАЯ КОМАНДА /test ВЫПОЛНЕНА!")
    await update.message.reply_text("✅ /test работает!")

def setup_jobs(app):
    """Настройка периодических задач"""
    try:
        from handlers.jobs import setup_all_jobs
        setup_all_jobs(app)
    except Exception as e:
        print(f"⚠️ Ошибка настройки задач: {e}")

def main():
    print("\n" + "="*50)
    print("🚀 ЗАПУСК БОТА")
    print("="*50)
    
    # Создаём папки
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Настройка логирования
    setup_logger('bot')
    
    # База данных
    print("📦 Инициализация БД...")
    init_database()
    
    # Устанавливаем ID владельца
    set_owner_id(OWNER_ID)
    
    # Создание приложения
    print("🔌 Подключение к Telegram...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ТЕСТОВАЯ КОМАНДА (всегда работает)
    print("➕ Добавление тестовой команды /test")
    app.add_handler(CommandHandler("test", test_command))
    
    # Проверка доступности модулей
    print("\n🔍 ПРОВЕРКА МОДУЛЕЙ:")
    try:
        import commands
        print(f"  ✅ commands импортирован")
        
        # Проверим первый попавшийся файл
        for cmd in ['test', 'warn', 'info']:
            try:
                module = __import__(f'commands.{cmd}', fromlist=['register'])
                if hasattr(module, 'register'):
                    print(f"  ✅ commands.{cmd}.register существует")
                else:
                    print(f"  ❌ commands.{cmd}.register НЕ существует")
            except Exception as e:
                print(f"  ❌ commands.{cmd}: {e}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    print("\n📦 ЗАГРУЗКА КОМАНД ИЗ ПАПКИ commands/:")
    # Автоматическая регистрация всех команд
    register_all_commands(app)
    
    # Системные обработчики
    print("\n➕ Добавление системных обработчиков...")
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Периодические задачи
    print("⏰ Настройка периодических задач...")
    setup_jobs(app)
    
    print("\n" + "="*50)
    print("✅ БОТ ГОТОВ К РАБОТЕ!")
    print("="*50 + "\n")
    
    # Запуск
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()