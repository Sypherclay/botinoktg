"""
БЭКАПЫ БАЗЫ ДАННЫХ
/backup
"""
import os
import shutil
import glob
from datetime import datetime
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
from permissions import is_admin
from logger import log_admin_action

async def cmd_backup(update, context):
    """Ручное создание бэкапа"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        # Папка для бэкапов
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/bot_database_{timestamp}.db"
        
        if os.path.exists("bot_database.db"):
            shutil.copy2("bot_database.db", backup_file)
            size = os.path.getsize(backup_file) / 1024
            
            # Количество бэкапов
            count = len(glob.glob(f"{backup_dir}/bot_database_*.db"))
            
            admin_name = update.effective_user.full_name
            
            log_admin_action(
                admin_id=user_id,
                admin_name=admin_name,
                action="Создал бэкап",
                details=f"{size:.1f} KB"
            )
            
            await update.message.reply_text(
                f"✅ <b>Бэкап создан!</b>\n\n"
                f"📁 Файл: <code>{backup_file}</code>\n"
                f"📊 Размер: {size:.1f} KB\n"
                f"📦 Всего бэкапов: {count}\n\n"
                f"🔄 Автобэкап каждый день в 03:00\n"
                f"🗑️ Старые (старше 7 дней) удаляются",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text("❌ Файл БД не найден")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

def register(app):
    app.add_handler(CommandHandler("backup", cmd_backup))