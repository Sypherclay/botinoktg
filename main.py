#!/usr/bin/env python3
"""
ГЛАВНЫЙ ФАЙЛ БОТА - РАДИКАЛЬНАЯ ВЕРСИЯ
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

# Простая функция для отладки
async def debug_all_messages(update, context):
    """Ловит ВСЕ сообщения для отладки"""
    if update.message:
        text = update.message.text or "[медиа]"
        print(f"\n📨 ВСЕ СООБЩЕНИЯ: {text}")
        print(f"   Это команда? {update.message.text and update.message.text.startswith(('!', '/'))}")

async def handle_non_command(update, context):
    """Обработка НЕ-команд"""
    if update.message and update.message.text:
        if update.message.text.startswith(('!', '/')):
            # Это команда - игнорируем, она будет обработана отдельно
            return
    print(f"📝 Не-команда: {update.message.text if update.message else 'без текста'}")

def setup_jobs(app):
    try:
        from handlers.jobs import setup_all_jobs
        setup_all_jobs(app)
    except Exception as e:
        print(f"⚠️ Ошибка задач: {e}")

def main():
    print("\n" + "="*50)
    print("🚀 ЗАПУСК БОТА (ДИАГНОСТИКА)")
    print("="*50)
    
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    setup_logger('bot')
    init_database()
    set_owner_id(OWNER_ID)
    
    print("🔌 Подключение к Telegram...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    # 1. ДЕБАГГЕР - ловит ВСЁ (самый первый)
    app.add_handler(MessageHandler(filters.ALL, debug_all_messages), group=-1)
    
    # 2. ТЕСТОВАЯ КОМАНДА (самая простая)
    async def test_cmd(update, context):
        print("✅ ТЕСТОВАЯ КОМАНДА СРАБОТАЛА!")
        await update.message.reply_text("✅ Работает!")
    
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^!тест\b'), 
        test_cmd
    ))
    
    # 3. ВСЕ ОСТАЛЬНЫЕ КОМАНДЫ ИЗ ПАПКИ
    print("\n📦 Загрузка команд...")
    register_all_commands(app)
    
    # 4. Callback обработчик
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # 5. Обработчик НЕ-команд (только если это не команда)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_non_command
    ))
    
    print("\n⏰ Настройка задач...")
    setup_jobs(app)
    
    print("\n" + "="*50)
    print("✅ БОТ ГОТОВ!")
    print("="*50 + "\n")
    
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")