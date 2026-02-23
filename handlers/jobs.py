"""
ПЕРИОДИЧЕСКИЕ ЗАДАЧИ
"""
import datetime  # ← ВАЖНО: импортируем модуль, а не класс
import os
import shutil
import glob
import sqlite3
from database import DB_PATH, get_setting, cleanup_old_groups
from logger import log_system_event, log_error

# ========== БЭКАПЫ ==========

async def create_database_backup(context):
    """Автоматическое создание бэкапа"""
    try:
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/bot_database_{timestamp}.db"
        
        if os.path.exists("bot_database.db"):
            shutil.copy2("bot_database.db", backup_file)
            size = os.path.getsize(backup_file) / 1024
            print(f"💾 Автобэкап: {backup_file} ({size:.1f} KB)")
            
            # Удаляем старые (старше 7 дней)
            now = datetime.datetime.now().timestamp()
            deleted = 0
            for old in glob.glob(f"{backup_dir}/bot_database_*.db"):
                if os.path.getmtime(old) < now - 7 * 86400:
                    os.remove(old)
                    deleted += 1
            
            if deleted:
                print(f"🗑️ Удалено старых бэкапов: {deleted}")
        else:
            log_error("BACKUP", "Файл БД не найден")
            
    except Exception as e:
        log_error("BACKUP_ERROR", str(e))

# ========== ОТПУСКА ==========

async def check_vacation_end(context):
    """Проверка окончания отпусков"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, end_date FROM vacations WHERE active = 1')
        vacations = cursor.fetchall()
        conn.close()
        
        now = datetime.datetime.now()
        
        for uid, end_str in vacations:
            end = datetime.datetime.fromisoformat(end_str)
            
            if end < now:
                # Завершаем отпуск
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('UPDATE vacations SET active = 0 WHERE user_id = ?', (uid,))
                conn.commit()
                conn.close()
                
                # Уведомление
                try:
                    await context.bot.send_message(
                        chat_id=uid,
                        text="🏖️ Ваш отпуск закончился! Добро пожаловать обратно!",
                        parse_mode='HTML'
                    )
                except:
                    pass
                
                print(f"📢 Отпуск закончился: {uid}")
                
    except Exception as e:
        log_error("VACATION_CHECK", str(e))

# ========== ЗАРПЛАТЫ ==========

async def check_salaries(context):
    """Ежедневная проверка зарплат"""
    try:
        from commands.salary import calculate_salaries
        await calculate_salaries(context)
    except Exception as e:
        log_error("SALARY_CHECK", str(e))

# ========== НАПОМИНАНИЯ О НЕАКТИВНОСТИ ==========

async def check_inactivity(context):
    """Проверка неактивных пользователей"""
    try:
        from commands.reminders import check_inactivity_reminders
        await check_inactivity_reminders(context)
    except Exception as e:
        log_error("INACTIVITY_CHECK", str(e))

# ========== ОЧИСТКА БД ==========

async def cleanup_db(context):
    """Очистка старых данных"""
    try:
        cleanup_old_groups(hours=24)
        log_system_event("Очистка медиа-групп выполнена")
    except Exception as e:
        log_error("DB_CLEANUP", str(e))

# ========== НАСТРОЙКА ВСЕХ ЗАДАЧ ==========

def setup_all_jobs(app):
    """Настройка всех периодических задач"""
    job = app.job_queue
    
    if not job:
        print("⚠️ JobQueue не доступен")
        return
    
    # Бэкап каждый день в 03:00 - ИСПРАВЛЕНО!
    job.run_daily(
        callback=create_database_backup,
        time=datetime.time(3, 0),  # ← ИСПРАВЛЕНО! было datetime.time(hour=3, minute=0)
        days=(0,1,2,3,4,5,6),
        name="daily_backup"
    )
    
    # Бэкап при запуске (через 5 минут)
    job.run_once(
        callback=create_database_backup,
        when=300,
        name="startup_backup"
    )
    
    # Проверка отпусков каждый час
    job.run_repeating(
        callback=check_vacation_end,
        interval=3600,
        first=10,
        name="vacation_check"
    )
    
    # Проверка зарплат каждый день в 00:00
    job.run_daily(
        callback=check_salaries,
        time=datetime.time(0, 0),  # ← ИСПРАВЛЕНО
        days=(0,1,2,3,4,5,6),
        name="salary_check"
    )
    
    # Проверка неактивности каждые 6 часов
    job.run_repeating(
        callback=check_inactivity,
        interval=21600,
        first=30,
        name="inactivity_check"
    )
    
    # Очистка БД каждые 24 часа
    job.run_repeating(
        callback=cleanup_db,
        interval=86400,
        first=3600,
        name="db_cleanup"
    )
    
    log_system_event("Все периодические задачи настроены")
    print("✅ Периодические задачи настроены")