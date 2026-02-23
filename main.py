#!/usr/bin/env python3
"""
ГЛАВНЫЙ ФАЙЛ БОТА - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import logging
import os
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN
from commands import register_all_commands
from handlers.message_handler import handle_message
from keyboards.callback_handler import handle_callback_query
from database import init_database
from logger import setup_logger, log_bot_event
from user_resolver import set_owner_id
from config import OWNER_ID

def setup_jobs(app):
    """Настройка периодических задач"""
    from handlers.jobs import setup_all_jobs
    setup_all_jobs(app)

def main():
    # Создаём нужные папки
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Настройка логирования - ИСПРАВЛЕНО!
    setup_logger('bot')  # ← БЫЛО: setup_logger()
    
    init_database()
    set_owner_id(OWNER_ID)
    
    # Создание приложения
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Автоматическая регистрация ВСЕХ команд
    register_all_commands(app)
    log_bot_event("✅ Все команды загружены")
    
    # Системные обработчики
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Периодические задачи
    setup_jobs(app)
    
    log_bot_event("🚀 Бот запущен!")
    print("\n" + "="*50)
    print("✅ БОТ ГОТОВ К РАБОТЕ!")
    print("="*50 + "\n")
    
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log_bot_event("👋 Бот остановлен")
        print("\n👋 Бот остановлен")