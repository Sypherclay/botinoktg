"""
СИСТЕМА ЛОГИРОВАНИЯ
Ведение логов для мониторинга и отладки
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Создаём папку для логов
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logger(name, log_file=None, level=logging.INFO):
    """Настройка логгера"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Консоль
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # Файл
    if log_file:
        today = datetime.now().strftime('%Y-%m-%d')
        log_path = Path(LOG_DIR) / f"{today}_{log_file}"
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Основные логгеры
bot_logger = setup_logger('bot', 'bot.log')
admin_logger = setup_logger('admin', 'admin.log')
user_logger = setup_logger('user', 'user.log')
error_logger = setup_logger('error', 'errors.log', logging.ERROR)

def log_bot_event(message, level='info'):
    """Логирование событий бота"""
    level = level.lower()
    if level == 'info':
        bot_logger.info(message)
    elif level == 'warning':
        bot_logger.warning(message)
    elif level == 'error':
        bot_logger.error(message)
    elif level == 'debug':
        bot_logger.debug(message)

def log_admin_action(admin_id, admin_name, action, target=None, details=None):
    """Логирование действий администраторов"""
    log = f"👑 ADMIN: {admin_name} ({admin_id}) - {action}"
    if target:
        log += f" - Цель: {target}"
    if details:
        log += f" - Детали: {details}"
    
    admin_logger.info(log)
    bot_logger.info(log)

def log_user_action(user_id, user_name, action, details=None):
    """Логирование действий пользователей"""
    log = f"👤 USER: {user_name} ({user_id}) - {action}"
    if details:
        log += f" - {details}"
    
    user_logger.info(log)

def log_error(error_type, error_message, user_id=None, chat_id=None):
    """Логирование ошибок"""
    log = f"❌ ERROR: {error_type} - {error_message}"
    if user_id:
        log += f" - User: {user_id}"
    if chat_id:
        log += f" - Chat: {chat_id}"
    
    error_logger.error(log)
    bot_logger.error(log)

def log_command(command, user_id, user_name, chat_id=None, result=None):
    """Логирование использования команд"""
    log = f"📝 COMMAND: {command} - {user_name} ({user_id})"
    if chat_id:
        log += f" - Chat: {chat_id}"
    if result:
        log += f" - Result: {result}"
    
    user_logger.info(log)

def log_vacation(user_id, user_name, days, action):
    """Логирование отпусков"""
    log = f"🏖️ VACATION: {user_name} ({user_id}) - {action} {days} дней"
    user_logger.info(log)
    bot_logger.info(log)

def log_warning_issued(admin_id, admin_name, user_id, user_name, reason):
    """Логирование выданных выговоров"""
    log = f"⚠️ WARNING: {admin_name} ({admin_id}) выдал выговор {user_name} ({user_id}) - Причина: {reason}"
    admin_logger.info(log)
    bot_logger.info(log)

def log_rank_change(admin_id, admin_name, user_id, user_name, old_rank, new_rank):
    """Логирование изменения рангов"""
    log = f"🎖️ RANK: {admin_name} ({admin_id}) изменил ранг {user_name} ({user_id}) с '{old_rank}' на '{new_rank}'"
    admin_logger.info(log)
    bot_logger.info(log)

def log_kick(user_id, user_name, reason, by_admin=None):
    """Логирование киков"""
    if by_admin:
        log = f"🚫 KICK: {user_name} ({user_id}) кикнут администратором {by_admin} - Причина: {reason}"
    else:
        log = f"🚫 KICK: {user_name} ({user_id}) кикнут автоматически - Причина: {reason}"
    
    admin_logger.info(log)
    bot_logger.info(log)

def log_system_event(event, details=None):
    """Логирование системных событий"""
    log = f"⚙️ SYSTEM: {event}"
    if details:
        log += f" - {details}"
    
    bot_logger.info(log)

def log_auto_warn(user_id, user_name, has_media, has_text, count):
    """Логирование авто-варна"""
    media_type = "медиа" if has_media else ""
    text_type = "текст" if has_text else ""
    if media_type and text_type:
        warn_type = "медиа+текст"
    elif media_type:
        warn_type = "только медиа"
    elif text_type:
        warn_type = "только текст"
    else:
        warn_type = "пустое сообщение"
    
    log = f"⚠️ АВТО-ВАРН: {user_name} ({user_id}) - {warn_type} (всего: {count})"
    bot_logger.info(log)
    print(log)

def cleanup_old_logs(days_to_keep=30):
    """Очистка старых логов"""
    try:
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        
        for log_file in glob.glob(f"{LOG_DIR}/*.log"):
            file_date_str = Path(log_file).name.split('_')[0]
            try:
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                if file_date < cutoff:
                    os.remove(log_file)
                    bot_logger.info(f"🗑️ Удален старый лог: {log_file}")
            except ValueError:
                continue
    except Exception as e:
        error_logger.error(f"Ошибка очистки логов: {e}")

# Импорты для функций выше
from datetime import timedelta
import glob