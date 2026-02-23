"""
ПОЛНАЯ БАЗА ДАННЫХ
Все функции из твоего database_sqlite.py в одном файле
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = 'bot_database.db'

# ========== ИНИЦИАЛИЗАЦИЯ ==========

def init_database():
    """Создание всех таблиц"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ===== ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            chat_id TEXT,
            username TEXT,
            name TEXT,
            count INTEGER DEFAULT 0,
            albums INTEGER DEFAULT 0,
            media_messages INTEGER DEFAULT 0,
            punishments INTEGER DEFAULT 0,
            rank TEXT DEFAULT 'user',
            last_active TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    # ===== ТАБЛИЦА ТЕМ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            chat_id TEXT,
            topic_id TEXT,
            topic_name TEXT,
            messages_count INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, topic_id)
        )
    ''')
    
    # ===== ТАБЛИЦА АКТИВНОСТИ В ТЕМАХ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_topics (
            chat_id TEXT,
            topic_id TEXT,
            user_id INTEGER,
            messages_count INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, topic_id, user_id)
        )
    ''')
    
    # ===== ТАБЛИЦА ЗАРПЛАТ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary (
            user_id INTEGER PRIMARY KEY,
            salary_counter INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 0,
            last_payout TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА ВЫГОВОРОВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id TEXT,
            reason TEXT,
            warned_by INTEGER,
            warned_by_name TEXT,
            date TEXT,
            active INTEGER DEFAULT 1,
            removed_date TEXT,
            removed_by INTEGER,
            removed_by_name TEXT,
            removed_reason TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА КАСТОМНЫХ НИКОВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_warnings (
            user_id INTEGER PRIMARY KEY,
            custom_nick TEXT,
            max_warnings INTEGER DEFAULT 3
        )
    ''')
    
    # ===== ТАБЛИЦА ОТПУСКОВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vacations (
            user_id INTEGER PRIMARY KEY,
            start_date TEXT,
            end_date TEXT,
            active INTEGER DEFAULT 1,
            used_days INTEGER DEFAULT 0
        )
    ''')
    
    # ===== ТАБЛИЦА НАСТРОЕК =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА МЕДИА ГРУПП =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_groups (
            group_id TEXT PRIMARY KEY,
            first_seen TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА АВТО-ВАРНОВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auto_warn (
            topic_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1
        )
    ''')
    
    # ===== ТАБЛИЦА БЕЛОГО СПИСКА =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whitelist (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    # ===== ТАБЛИЦА СЧЁТЧИКОВ АВТО-ВАРНОВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auto_warn_counts (
            user_id INTEGER,
            chat_id TEXT,
            count INTEGER DEFAULT 0,
            last_warn TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    # ===== ТАБЛИЦА НАПОМИНАНИЙ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            user_id INTEGER,
            chat_id TEXT,
            last_active TEXT,
            notified_1d INTEGER DEFAULT 0,
            notified_3d INTEGER DEFAULT 0,
            notified_7d INTEGER DEFAULT 0,
            notified_14d INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    # ===== ТАБЛИЦА НАСТРОЕК НАПОМИНАНИЙ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminder_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            enabled INTEGER DEFAULT 1,
            intervals TEXT DEFAULT '{"1_day": true, "3_days": true, "7_days": true, "14_days": true}',
            sent_reminders TEXT DEFAULT '{}'
        )
    ''')
    
    # ===== ТАБЛИЦА ЮБИЛЕЕВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS milestones (
            chat_id TEXT,
            topic_id TEXT,
            user_id INTEGER,
            message_count INTEGER DEFAULT 0,
            last_milestone INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, topic_id, user_id)
        )
    ''')
    
    # ===== ТАБЛИЦА РАНГОВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ranks (
            user_id INTEGER PRIMARY KEY,
            rank TEXT DEFAULT 'user',
            assigned_by INTEGER,
            assigned_date TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА МОДЕРАТОРОВ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moderators (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_date TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА ПРИВЕТСТВИЙ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS welcome_settings (
            chat_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            message TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА ИСТОРИИ ВЫПЛАТ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payout_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            total_paid INTEGER,
            users_count INTEGER,
            rate INTEGER
        )
    ''')
    
    # ===== ТАБЛИЦА СЕССИЙ ПОЛЬЗОВАТЕЛЕЙ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            chat_id TEXT,
            topic_id TEXT,
            user_id_selected TEXT,
            period TEXT,
            step TEXT,
            last_updated TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА ЖАЛОБ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_complaints (
            user_id INTEGER PRIMARY KEY,
            complaint_count INTEGER DEFAULT 0,
            last_complaint_date TEXT
        )
    ''')
    
    # ===== ТАБЛИЦА НАГРАД =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints_rewards (
            user_id INTEGER,
            reward_type TEXT,
            achieved_date TEXT,
            PRIMARY KEY (user_id, reward_type)
        )
    ''')
    
    # Настройки по умолчанию
    default_settings = [
        ('rate_per_punishment', '10'),
        ('max_warnings', '3'),
        ('kick_topic_id', None),
        ('payout_topic_id', None),
        ('topic_set_date', None),
        ('last_payout', None),
        ('next_payout', None),
        ('max_vacation_days', '14'),
        ('global_welcome_enabled', '1'),
        ('auto_warn_message', '⚠️ Некорректная подача. (См. закреплённое сообщение)'),
        ('milestone_topics', '[]'),
        ('admins', json.dumps([]))
    ]
    
    for key, value in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
    
    # Настройки напоминаний
    cursor.execute('''
        INSERT OR IGNORE INTO reminder_settings (id, enabled, intervals, sent_reminders)
        VALUES (1, 1, '{"1_day": true, "3_days": true, "7_days": true, "14_days": true}', '{}')
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

# ========== ПОЛЬЗОВАТЕЛИ ==========

def get_or_create_user(user_id, chat_id, username='', name=''):
    """Получить или создать пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users WHERE user_id = ? AND chat_id = ?
    ''', (user_id, chat_id))
    
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, chat_id, username, name, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, chat_id, username, name, datetime.now().isoformat()))
        conn.commit()
    
    conn.close()

def update_user_stats(user_id, chat_id, has_media, has_text, is_album, is_auto_warn_topic=False):
    """Обновить статистику пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # last_active
    cursor.execute('''
        UPDATE users SET last_active = ? 
        WHERE user_id = ? AND chat_id = ?
    ''', (datetime.now().isoformat(), user_id, chat_id))
    
    # счётчики
    cursor.execute('''
        UPDATE users 
        SET count = count + ?,
            albums = albums + ?,
            media_messages = media_messages + ?
        WHERE user_id = ? AND chat_id = ?
    ''', (
        0 if is_album else 1,
        1 if is_album else 0,
        1 if (has_media and not has_text) else 0,
        user_id, chat_id
    ))
    
    # наказание (медиа+текст) - только если тема в авто-варнах
    if has_media and has_text and is_auto_warn_topic:
        cursor.execute('''
            UPDATE users 
            SET punishments = punishments + 1
            WHERE user_id = ? AND chat_id = ?
        ''', (user_id, chat_id))
        
        # зарплата
        cursor.execute('''
            INSERT INTO salary (user_id, salary_counter, balance)
            VALUES (?, 1, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                salary_counter = salary_counter + 1
        ''', (user_id,))
    
    conn.commit()
    conn.close()

def get_user_punishments(user_id, chat_id):
    """Количество наказаний"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT punishments FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def get_user_info(user_id, chat_id):
    """Имя и username"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name, username FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    res = cursor.fetchone()
    conn.close()
    return res if res else (None, None)

def get_user_info_any_chat(user_id):
    """Имя из любого чата"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name, username FROM users WHERE user_id = ? LIMIT 1', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_user_by_username(username, chat_id):
    """Поиск по username"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, name FROM users WHERE username = ? AND chat_id = ?', (username, chat_id))
    res = cursor.fetchone()
    conn.close()
    return res

def get_all_users_in_chat(chat_id):
    """Все пользователи чата"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, name, username FROM users WHERE chat_id = ?', (chat_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def user_exists_in_chat(user_id, chat_id):
    """Проверка существования"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def get_all_users_count(chat_id):
    """Количество пользователей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE chat_id = ?', (chat_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ========== ТЕМЫ ==========

def get_or_create_topic(chat_id, topic_id, topic_name=''):
    """Получить или создать тему"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM topics WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
    topic = cursor.fetchone()
    if not topic and topic_name:
        cursor.execute('INSERT INTO topics (chat_id, topic_id, topic_name) VALUES (?, ?, ?)', (chat_id, topic_id, topic_name))
        conn.commit()
    conn.close()

def update_topic_stats(chat_id, topic_id, user_id):
    """Обновить статистику темы"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE topics SET messages_count = messages_count + 1 WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
    
    cursor.execute('''
        INSERT INTO user_topics (chat_id, topic_id, user_id, messages_count)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(chat_id, topic_id, user_id) DO UPDATE SET
            messages_count = messages_count + 1
    ''', (chat_id, topic_id, user_id))
    
    conn.commit()
    conn.close()

def get_user_topic_count(chat_id, topic_id, user_id):
    """Сообщения пользователя в теме"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if topic_id is None:
        cursor.execute('SELECT SUM(messages_count) FROM user_topics WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    else:
        cursor.execute('SELECT messages_count FROM user_topics WHERE chat_id = ? AND topic_id = ? AND user_id = ?', (chat_id, topic_id, user_id))
    
    res = cursor.fetchone()
    conn.close()
    return res[0] if res and res[0] else 0

def get_chat_topics(chat_id):
    """Список тем чата"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT topic_id, topic_name, messages_count FROM topics WHERE chat_id = ? ORDER BY messages_count DESC', (chat_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_topic_users(chat_id, topic_id=None):
    """Пользователи темы со статистикой"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if topic_id is None:
        cursor.execute('''
            SELECT ut.user_id, u.name, u.username, SUM(ut.messages_count) as total
            FROM user_topics ut
            JOIN users u ON ut.user_id = u.user_id AND ut.chat_id = u.chat_id
            WHERE ut.chat_id = ?
            GROUP BY ut.user_id
            ORDER BY total DESC
        ''', (chat_id,))
    else:
        cursor.execute('''
            SELECT ut.user_id, u.name, u.username, ut.messages_count
            FROM user_topics ut
            JOIN users u ON ut.user_id = u.user_id AND ut.chat_id = u.chat_id
            WHERE ut.chat_id = ? AND ut.topic_id = ?
            ORDER BY ut.messages_count DESC
        ''', (chat_id, topic_id))
    
    res = cursor.fetchall()
    conn.close()
    return res

def add_user_to_topic(chat_id, topic_id, user_id, message_count=0):
    """Добавить пользователя в тему"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_topics (chat_id, topic_id, user_id, messages_count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chat_id, topic_id, user_id) DO NOTHING
    ''', (chat_id, topic_id, user_id, message_count))
    conn.commit()
    conn.close()

# ========== ЗАРПЛАТЫ ==========

def get_salary_counter(user_id):
    """Счётчик зарплат"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT salary_counter FROM salary WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def add_to_salary_counter(user_id, amount=1):
    """Добавить к счётчику"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO salary (user_id, salary_counter, balance)
        VALUES (?, ?, 0)
        ON CONFLICT(user_id) DO UPDATE SET
            salary_counter = salary_counter + ?
    ''', (user_id, amount, amount))
    conn.commit()
    conn.close()
    return get_salary_counter(user_id)

def reset_salary_counter(user_id):
    """Сбросить счётчик"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE salary SET salary_counter = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    """Баланс"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM salary WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def add_to_balance(user_id, amount):
    """Начислить"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO salary (user_id, salary_counter, balance)
        VALUES (?, 0, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            balance = balance + ?
    ''', (user_id, amount, amount))
    conn.commit()
    conn.close()
    return get_user_balance(user_id)

def subtract_from_balance(user_id, amount):
    """Списать"""
    current = get_user_balance(user_id)
    if current < amount:
        return False, current
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE salary SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    return True, current - amount

def get_all_users_with_salary(chat_id):
    """Пользователи с данными о зарплате"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.user_id, u.name, u.username, u.punishments, 
               s.salary_counter, s.balance
        FROM users u
        LEFT JOIN salary s ON u.user_id = s.user_id
        WHERE u.chat_id = ? AND (u.punishments > 0 OR s.salary_counter > 0 OR s.balance > 0)
    ''', (chat_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_payout_settings():
    """Настройки выплат"""
    settings = {}
    keys = ['payout_topic_id', 'topic_set_date', 'last_payout', 'next_payout', 'rate_per_punishment']
    
    for key in keys:
        val = get_setting(key)
        if val is not None:
            settings[key] = val
    
    if 'rate_per_punishment' not in settings:
        settings['rate_per_punishment'] = '10'
    
    return settings

def save_payout_settings(settings):
    """Сохранить настройки выплат"""
    for key, val in settings.items():
        if val is not None:
            set_setting(key, str(val))
        else:
            set_setting(key, None)

def add_payout_history(record):
    """Добавить запись в историю"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payout_history (date, total_paid, users_count, rate)
        VALUES (?, ?, ?, ?)
    ''', (record['date'], record['total_paid'], record['users_count'], record['rate']))
    conn.commit()
    conn.close()

def get_payout_history(limit=10):
    """История выплат"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT date, total_paid, users_count, rate FROM payout_history ORDER BY date DESC LIMIT ?', (limit,))
    res = cursor.fetchall()
    conn.close()
    return res

# ========== ВЫГОВОРЫ ==========

def add_warning(user_id, chat_id, reason, warned_by, warned_by_name):
    """Добавить выговор"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO warnings (user_id, chat_id, reason, warned_by, warned_by_name, date, active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (user_id, chat_id, reason, warned_by, warned_by_name, date))
    
    cursor.execute('''
        INSERT INTO user_warnings (user_id, max_warnings)
        VALUES (?, 3)
        ON CONFLICT(user_id) DO NOTHING
    ''', (user_id,))
    
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM warnings WHERE user_id = ? AND chat_id = ? AND active = 1', (user_id, chat_id))
    active = cursor.fetchone()[0]
    conn.close()
    return active

def get_user_warnings(user_id, chat_id, active_only=True):
    """Получить выговоры"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if active_only:
        cursor.execute('SELECT id, reason, warned_by_name, date, warned_by FROM warnings WHERE user_id = ? AND chat_id = ? AND active = 1 ORDER BY date DESC', (user_id, chat_id))
    else:
        cursor.execute('SELECT id, reason, warned_by_name, date, warned_by, active, removed_date, removed_by_name, removed_reason FROM warnings WHERE user_id = ? AND chat_id = ? ORDER BY date DESC', (user_id, chat_id))
    
    res = cursor.fetchall()
    conn.close()
    return res

def get_warnings_count(user_id, chat_id):
    """Количество активных выговоров"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM warnings WHERE user_id = ? AND chat_id = ? AND active = 1', (user_id, chat_id))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def remove_last_warning(user_id, chat_id, removed_by, removed_by_name):
    """Снять последний выговор"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, reason FROM warnings WHERE user_id = ? AND chat_id = ? AND active = 1 ORDER BY date DESC LIMIT 1', (user_id, chat_id))
    res = cursor.fetchone()
    
    if not res:
        conn.close()
        return None
    
    wid, reason = res
    
    cursor.execute('''
        UPDATE warnings 
        SET active = 0, removed_date = ?, removed_by = ?, removed_by_name = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), removed_by, removed_by_name, wid))
    
    conn.commit()
    conn.close()
    return reason

def remove_all_warnings(user_id, chat_id, removed_by, removed_by_name, reason="Сняты при кике"):
    """Снять все выговоры"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE warnings 
        SET active = 0, removed_date = ?, removed_by = ?, removed_by_name = ?, removed_reason = ?
        WHERE user_id = ? AND chat_id = ? AND active = 1
    ''', (datetime.now().isoformat(), removed_by, removed_by_name, reason, user_id, chat_id))
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def get_all_users_with_warnings(chat_id):
    """Все пользователи с выговорами"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT w.user_id, u.name, u.username, COUNT(*) as count
        FROM warnings w
        LEFT JOIN users u ON w.user_id = u.user_id AND w.chat_id = u.chat_id
        WHERE w.chat_id = ? AND w.active = 1
        GROUP BY w.user_id
        ORDER BY count DESC
    ''', (chat_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_user_max_warnings(user_id):
    """Максимум выговоров для пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT max_warnings FROM user_warnings WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 3

def set_user_max_warnings(user_id, max_count):
    """Установить максимум"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_warnings (user_id, max_warnings)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET max_warnings = ?
    ''', (user_id, max_count, max_count))
    conn.commit()
    conn.close()
    return True

def set_user_custom_nick(user_id, nick):
    """Установить кастомный ник"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_warnings (user_id, custom_nick, max_warnings)
        VALUES (?, ?, 3)
        ON CONFLICT(user_id) DO UPDATE SET custom_nick = ?
    ''', (user_id, nick, nick))
    conn.commit()
    conn.close()

def get_user_custom_nick(user_id):
    """Получить кастомный ник"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT custom_nick FROM user_warnings WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def get_user_id_by_custom_nick(nick):
    """Найти ID по кастомному нику"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM user_warnings WHERE LOWER(custom_nick) = LOWER(?)', (nick,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def delete_user_warnings(user_id, chat_id):
    """Удалить все выговоры"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM warnings WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted
    
# ========== РАСШИРЕННЫЕ ФУНКЦИИ ДЛЯ ВАРНОВ ==========

def add_warning_v2(user_id, chat_id, reason, warned_by, warned_by_name, warn_type="ручной"):
    """Добавить варн с причиной (новая версия)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date = datetime.now().isoformat()
    
    # Добавляем запись в warnings (используем ту же таблицу, но с пометкой типа)
    cursor.execute('''
        INSERT INTO warnings 
        (user_id, chat_id, reason, warned_by, warned_by_name, date, active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (user_id, chat_id, f"[{warn_type}] {reason}", warned_by, warned_by_name, date))
    
    # Также увеличиваем счётчик в auto_warn_counts для совместимости
    cursor.execute('''
        INSERT INTO auto_warn_counts (user_id, chat_id, count, last_warn)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            count = count + 1,
            last_warn = ?
    ''', (user_id, chat_id, date, date))
    
    conn.commit()
    
    # Получаем общее количество варнов (активных)
    cursor.execute('''
        SELECT COUNT(*) FROM warnings 
        WHERE user_id = ? AND chat_id = ? AND active = 1 
        AND reason LIKE '[ручной]%'
    ''', (user_id, chat_id))
    total = cursor.fetchone()[0]
    
    conn.close()
    return total

def get_user_warns_with_reasons(user_id, chat_id, active_only=True):
    """Получить все варны пользователя с причинами"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if active_only:
        cursor.execute('''
            SELECT id, reason, warned_by_name, date, warned_by
            FROM warnings 
            WHERE user_id = ? AND chat_id = ? AND active = 1 
            AND reason LIKE '[ручной]%'
            ORDER BY date DESC
        ''', (user_id, chat_id))
    else:
        cursor.execute('''
            SELECT id, reason, warned_by_name, date, warned_by, active,
                   removed_date, removed_by_name, removed_reason
            FROM warnings 
            WHERE user_id = ? AND chat_id = ? AND reason LIKE '[ручной]%'
            ORDER BY date DESC
        ''', (user_id, chat_id))
    
    res = cursor.fetchall()
    conn.close()
    return res

def get_all_users_with_warns(chat_id):
    """Получить всех пользователей с активными варнами и их причинами"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT w.user_id, u.name, u.username, w.reason, w.date, w.warned_by_name
        FROM warnings w
        LEFT JOIN users u ON w.user_id = u.user_id AND w.chat_id = u.chat_id
        WHERE w.chat_id = ? AND w.active = 1 AND w.reason LIKE '[ручной]%'
        ORDER BY w.date DESC
    ''', (chat_id,))
    
    res = cursor.fetchall()
    conn.close()
    return res

def remove_last_warn(user_id, chat_id, removed_by, removed_by_name):
    """Снять последний активный варн (не выговор!)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Находим последний активный варн
    cursor.execute('''
        SELECT id, reason FROM warnings 
        WHERE user_id = ? AND chat_id = ? AND active = 1 
        AND reason LIKE '[ручной]%'
        ORDER BY date DESC LIMIT 1
    ''', (user_id, chat_id))
    
    res = cursor.fetchone()
    
    if not res:
        conn.close()
        return None
    
    warn_id, reason = res
    
    # Помечаем как снятый
    cursor.execute('''
        UPDATE warnings 
        SET active = 0, 
            removed_date = ?, 
            removed_by = ?, 
            removed_by_name = ?,
            removed_reason = 'Снят вручную'
        WHERE id = ?
    ''', (datetime.now().isoformat(), removed_by, removed_by_name, warn_id))
    
    # Также уменьшаем счётчик в auto_warn_counts
    cursor.execute('''
        UPDATE auto_warn_counts 
        SET count = CASE WHEN count > 0 THEN count - 1 ELSE 0 END
        WHERE user_id = ? AND chat_id = ?
    ''', (user_id, chat_id))
    
    conn.commit()
    conn.close()
    return reason

# ========== ОТПУСКА ==========

def set_vacation(user_id, start_date, end_date):
    """Установить отпуск"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    days = (end - start).days
    
    cursor.execute('''
        INSERT INTO vacations (user_id, start_date, end_date, active, used_days)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            start_date = ?, end_date = ?, active = 1, used_days = used_days + ?
    ''', (user_id, start_date, end_date, days, start_date, end_date, days))
    
    conn.commit()
    conn.close()

def get_vacation(user_id):
    """Информация об отпуске"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT start_date, end_date, used_days FROM vacations WHERE user_id = ? AND active = 1', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_vacation_info(user_id):
    """Алиас"""
    return get_vacation(user_id)

def end_vacation(user_id):
    """Завершить отпуск"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE vacations SET active = 0 WHERE user_id = ? AND active = 1', (user_id,))
    conn.commit()
    conn.close()

def reset_all_vacations():
    """Сбросить все отпуска"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vacations')
    conn.commit()
    conn.close()

def get_vacation_settings():
    """Настройки отпусков"""
    max_days = int(get_setting('max_vacation_days', '14'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM vacations WHERE active = 1')
    count = cursor.fetchone()[0]
    conn.close()
    return {'max_days': max_days, 'users_count': count}

def delete_user_vacation(user_id):
    """Удалить данные отпуска"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vacations WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_user_vacation_info_db(user_id):
    """Информация об отпуске из БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT used_days, active FROM vacations WHERE user_id = ? AND active = 1', (user_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        used, active = res
        return {'used': used, 'active': bool(active)}
    return {'used': 0, 'active': False}

def save_user_vacation_info(user_id, used_days, active=True):
    """Сохранить информацию об отпуске"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO vacations (user_id, used_days, active)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET used_days = ?, active = ?
    ''', (user_id, used_days, 1 if active else 0, used_days, 1 if active else 0))
    conn.commit()
    conn.close()

# ========== НАСТРОЙКИ ==========

def get_setting(key, default=None):
    """Получить настройку"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else default

def set_setting(key, value):
    """Установить настройку"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = ?
    ''', (key, value, value))
    conn.commit()
    conn.close()

def get_kick_topic_id():
    """Тема для киков"""
    return get_setting('kick_topic_id')

def set_kick_topic_id(topic_id):
    """Установить тему для киков"""
    set_setting('kick_topic_id', topic_id)

# ========== МЕДИА ГРУППЫ ==========

def is_first_in_album(media_group_id):
    """Проверить, первое ли сообщение в альбоме"""
    if not media_group_id:
        return True
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM media_groups WHERE group_id = ?', (media_group_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute('INSERT INTO media_groups (group_id, first_seen) VALUES (?, ?)', (media_group_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def cleanup_old_groups(hours=24):
    """Очистка старых групп"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    cursor.execute('DELETE FROM media_groups WHERE first_seen < ?', (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

# ========== АВТО-ВАРНЫ ==========

def is_auto_warn_enabled(topic_id):
    """Проверить, включены ли авто-варны в теме"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT enabled FROM auto_warn WHERE topic_id = ?', (topic_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] == 1 if res else False

def enable_auto_warn(topic_id):
    """Включить авто-варны"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO auto_warn (topic_id, enabled) VALUES (?, 1)
        ON CONFLICT(topic_id) DO UPDATE SET enabled = 1
    ''', (topic_id,))
    conn.commit()
    conn.close()

def disable_auto_warn(topic_id):
    """Выключить авто-варны"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO auto_warn (topic_id, enabled) VALUES (?, 0)
        ON CONFLICT(topic_id) DO UPDATE SET enabled = 0
    ''', (topic_id,))
    conn.commit()
    conn.close()

def get_auto_warn_topics():
    """Список тем с авто-варнами"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT topic_id FROM auto_warn WHERE enabled = 1')
    topics = [row[0] for row in cursor.fetchall()]
    conn.close()
    return topics

def add_auto_warn_topic(topic_id):
    """Добавить тему"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO auto_warn (topic_id, enabled) VALUES (?, 1)
        ON CONFLICT(topic_id) DO UPDATE SET enabled = 1
    ''', (topic_id,))
    conn.commit()
    conn.close()

def remove_auto_warn_topic(topic_id):
    """Удалить тему"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auto_warn WHERE topic_id = ?', (topic_id,))
    conn.commit()
    conn.close()

def delete_auto_warn_by_topic(topic_id):
    """Удалить настройки темы"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auto_warn WHERE topic_id = ?', (topic_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def is_whitelisted(user_id):
    """Проверить, в белом ли списке"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM whitelist WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def add_to_whitelist_db(user_id):
    """Добавить в белый список"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO whitelist (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_from_whitelist_db(user_id):
    """Удалить из белого списка"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM whitelist WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_whitelist():
    """Получить белый список"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM whitelist')
    whitelist = [row[0] for row in cursor.fetchall()]
    conn.close()
    return whitelist

def get_auto_warn_count(user_id, chat_id):
    """Количество авто-варнов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM auto_warn_counts WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def increment_auto_warn_count(user_id, chat_id):
    """Увеличить счётчик"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO auto_warn_counts (user_id, chat_id, count, last_warn)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            count = count + 1,
            last_warn = ?
    ''', (user_id, chat_id, now, now))
    
    conn.commit()
    
    cursor.execute('SELECT count FROM auto_warn_counts WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    new = cursor.fetchone()[0]
    conn.close()
    return new

def reset_auto_warn_count(user_id, chat_id):
    """Сбросить счётчик"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE auto_warn_counts SET count = 0 WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    conn.commit()
    conn.close()

def get_auto_warn_message():
    """Сообщение авто-варна"""
    msg = get_setting('auto_warn_message')
    if msg:
        return msg
    return "⚠️ Некорректная подача. (См. закреплённое сообщение)"

def set_auto_warn_message(message):
    """Установить сообщение"""
    set_setting('auto_warn_message', message)

def delete_user_auto_warn_count(user_id):
    """Удалить счётчик авто-варнов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auto_warn_counts WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ========== НАПОМИНАНИЯ ==========

def update_user_activity(user_id, chat_id):
    """Обновить время активности"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO reminders (user_id, chat_id, last_active, notified_1d, notified_3d, notified_7d, notified_14d)
        VALUES (?, ?, ?, 0, 0, 0, 0)
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            last_active = ?,
            notified_1d = 0,
            notified_3d = 0,
            notified_7d = 0,
            notified_14d = 0
    ''', (user_id, chat_id, now, now))
    
    conn.commit()
    conn.close()

def get_user_activity(user_id, chat_id):
    """Получить время активности"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT last_active FROM reminders WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def get_all_activities():
    """Все активности"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, chat_id, last_active FROM reminders')
    res = cursor.fetchall()
    conn.close()
    return res

def get_reminder_settings():
    """Настройки напоминаний"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT enabled, intervals, sent_reminders FROM reminder_settings WHERE id = 1')
    res = cursor.fetchone()
    conn.close()
    
    if not res:
        return {
            'enabled': True,
            'intervals': {'1_day': True, '3_days': True, '7_days': True, '14_days': True},
            'sent_reminders': {}
        }
    
    enabled, intervals_json, sent_json = res
    return {
        'enabled': bool(enabled),
        'intervals': json.loads(intervals_json),
        'sent_reminders': json.loads(sent_json)
    }

def save_reminder_settings(settings):
    """Сохранить настройки напоминаний"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE reminder_settings 
        SET enabled = ?, intervals = ?, sent_reminders = ?
        WHERE id = 1
    ''', (1 if settings['enabled'] else 0, json.dumps(settings['intervals']), json.dumps(settings.get('sent_reminders', {}))))
    conn.commit()
    conn.close()

def check_and_mark_reminder(reminder_key):
    """Проверить и отметить напоминание"""
    settings = get_reminder_settings()
    
    if reminder_key in settings.get('sent_reminders', {}):
        last = datetime.fromisoformat(settings['sent_reminders'][reminder_key])
        if datetime.now() - last < timedelta(days=7):
            return False
    
    settings['sent_reminders'][reminder_key] = datetime.now().isoformat()
    
    # Очистка старых
    cutoff = datetime.now() - timedelta(days=30)
    to_del = []
    for key, date_str in settings['sent_reminders'].items():
        try:
            if datetime.fromisoformat(date_str) < cutoff:
                to_del.append(key)
        except:
            to_del.append(key)
    
    for key in to_del:
        del settings['sent_reminders'][key]
    
    save_reminder_settings(settings)
    return True

def mark_reminder_sent(reminder_key):
    """Отметить как отправленное"""
    settings = get_reminder_settings()
    settings['sent_reminders'][reminder_key] = datetime.now().isoformat()
    save_reminder_settings(settings)

# ========== ЮБИЛЕИ ==========

def get_milestone_tracked_topics():
    """Темы для отслеживания юбилеев"""
    res = get_setting('milestone_topics')
    return json.loads(res) if res else []

def add_milestone_topic(topic_id):
    """Добавить тему"""
    topics = get_milestone_tracked_topics()
    if topic_id not in topics:
        topics.append(topic_id)
        set_setting('milestone_topics', json.dumps(topics))
    return topics

def remove_milestone_topic(topic_id):
    """Удалить тему"""
    topics = get_milestone_tracked_topics()
    if topic_id in topics:
        topics.remove(topic_id)
        set_setting('milestone_topics', json.dumps(topics))
    return topics

def clear_all_milestones():
    """Очистить все достижения"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE milestones SET last_milestone = 0')
    conn.commit()
    conn.close()

def get_milestone_message(count):
    """Сообщение для юбилея"""
    messages = {
        500: "{ник} Прекрасное начало🤔",
        1000: "{ник} душно то как 🥴",
        1500: "{ник} ты вообще спишь?🫩",
        2000: "{ник} вот бы ты столько раз за сервер проголосовал🥲",
        2500: "{ник} ты на дизеле что ли🧐",
        3000: "{ник} сюда ещё никто не доходил... Ты - легенда 🫡"
    }
    return messages.get(count)

def get_user_achieved_milestones(user_id, chat_id):
    """Достигнутые юбилеи"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT last_milestone FROM milestones WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    res = cursor.fetchone()
    conn.close()
    
    if not res:
        return []
    
    last = res[0]
    milestones = []
    std = [500, 1000, 1500, 2000, 2500, 3000]
    for m in std:
        if m <= last:
            milestones.append(m)
    return milestones

def add_user_milestone(user_id, chat_id, milestone):
    """Добавить достигнутый юбилей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT last_milestone FROM milestones WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    res = cursor.fetchone()
    current = res[0] if res else 0
    
    if milestone > current:
        cursor.execute('''
            INSERT INTO milestones (user_id, chat_id, message_count, last_milestone)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET last_milestone = ?
        ''', (user_id, chat_id, milestone, milestone))
    
    conn.commit()
    conn.close()

def update_milestone_count(chat_id, topic_id, user_id):
    """Обновить счётчик для юбилея"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO milestones (chat_id, topic_id, user_id, message_count, last_milestone)
        VALUES (?, ?, ?, 1, 0)
        ON CONFLICT(chat_id, topic_id, user_id) DO UPDATE SET
            message_count = message_count + 1
    ''', (chat_id, topic_id, user_id))
    
    conn.commit()
    
    cursor.execute('SELECT message_count FROM milestones WHERE chat_id = ? AND topic_id = ? AND user_id = ?', (chat_id, topic_id, user_id))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def set_last_milestone(chat_id, topic_id, user_id, milestone):
    """Установить последний юбилей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE milestones SET last_milestone = ? WHERE chat_id = ? AND topic_id = ? AND user_id = ?', (milestone, chat_id, topic_id, user_id))
    conn.commit()
    conn.close()

def get_milestone_count(chat_id, topic_id, user_id):
    """Количество сообщений для юбилея"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT message_count, last_milestone FROM milestones WHERE chat_id = ? AND topic_id = ? AND user_id = ?', (chat_id, topic_id, user_id))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 0)

def delete_user_milestones(user_id, chat_id):
    """Удалить юбилеи пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM milestones WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ========== РАНГИ ==========

def get_user_rank_db(user_id):
    """Получить ранг"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT rank FROM ranks WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 'user'

def set_user_rank_db(user_id, rank, assigned_by=None):
    """Установить ранг"""
    if rank not in ['owner', 'curator', 'deputy_curator', 'manager', 'moder', 'helper', 'user', 'helper_plus', 'custom']:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    assigned_date = datetime.now().isoformat() if assigned_by else None
    
    cursor.execute('''
        INSERT INTO ranks (user_id, rank, assigned_by, assigned_date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET rank = ?, assigned_by = ?, assigned_date = ?
    ''', (user_id, rank, assigned_by, assigned_date, rank, assigned_by, assigned_date))
    
    conn.commit()
    conn.close()
    return True

def get_all_users_with_rank(rank):
    """Все пользователи с рангом"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM ranks WHERE rank = ?', (rank,))
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def delete_user_rank(user_id):
    """Удалить ранг"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ranks WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ========== АДМИНИСТРИРОВАНИЕ ==========

def get_all_admins():
    """Список администраторов"""
    res = get_setting('admins')
    admins = json.loads(res) if res else []
    
    from config import OWNER_ID
    if OWNER_ID not in admins:
        admins.append(OWNER_ID)
        set_setting('admins', json.dumps(admins))
    
    return admins

def add_admin_db(user_id):
    """Добавить администратора"""
    admins = get_all_admins()
    if user_id not in admins:
        admins.append(user_id)
        set_setting('admins', json.dumps(admins))
    return admins

def remove_admin_db(user_id):
    """Удалить администратора"""
    from config import OWNER_ID
    if user_id == OWNER_ID:
        return get_all_admins()
    
    admins = get_all_admins()
    if user_id in admins:
        admins.remove(user_id)
        set_setting('admins', json.dumps(admins))
    return admins

def is_admin_db(user_id):
    """Проверить, является ли администратором"""
    admins = get_all_admins()
    from config import OWNER_ID
    return user_id in admins or user_id == OWNER_ID

def get_all_moderators_db():
    """Список модераторов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM moderators')
    mods = [row[0] for row in cursor.fetchall()]
    conn.close()
    return mods

def is_moderator_db(user_id):
    """Проверить, является ли модератором"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM moderators WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def add_moderator_db(user_id, added_by=None):
    """Добавить модератора"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    added_date = datetime.now().isoformat()
    cursor.execute('INSERT OR IGNORE INTO moderators (user_id, added_by, added_date) VALUES (?, ?, ?)', (user_id, added_by, added_date))
    conn.commit()
    conn.close()
    return True

def remove_moderator_db(user_id):
    """Удалить модератора"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM moderators WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def add_chat_to_db(chat_id):
    """Добавить чат для отслеживания"""
    set_setting(f'chat_{chat_id}', 'active')

def remove_chat_from_db(chat_id):
    """Удалить чат из отслеживания"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    set_setting(f'chat_{chat_id}', None)
    
    cursor.execute('DELETE FROM users WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM topics WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM user_topics WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM warnings WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM auto_warn_counts WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM reminders WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM milestones WHERE chat_id = ?', (chat_id,))
    
    conn.commit()
    conn.close()

def get_all_chats():
    """Список отслеживаемых чатов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT key FROM settings WHERE key LIKE "chat_%"')
    chats = [row[0].replace('chat_', '') for row in cursor.fetchall()]
    conn.close()
    return chats

def get_chat_stats(chat_id):
    """Статистика чата"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE chat_id = ?', (chat_id,))
    users = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(count) FROM users WHERE chat_id = ?', (chat_id,))
    msgs = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(punishments) FROM users WHERE chat_id = ?', (chat_id,))
    puns = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE chat_id = ? AND punishments > 0', (chat_id,))
    pun_users = cursor.fetchone()[0]
    
    conn.close()
    return {
        'users': users,
        'messages': msgs,
        'punishments': puns,
        'users_with_punishments': pun_users
    }

# ========== ПРИВЕТСТВИЯ ==========

def get_chat_welcome(chat_id):
    """Текст приветствия для чата"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT message FROM welcome_settings WHERE chat_id = ?', (chat_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def set_chat_welcome(chat_id, message):
    """Установить текст приветствия"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO welcome_settings (chat_id, message, enabled)
        VALUES (?, ?, 1)
        ON CONFLICT(chat_id) DO UPDATE SET message = ?
    ''', (chat_id, message, message))
    conn.commit()
    conn.close()

def enable_chat_welcome(chat_id):
    """Включить приветствия в чате"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO welcome_settings (chat_id, enabled)
        VALUES (?, 1)
        ON CONFLICT(chat_id) DO UPDATE SET enabled = 1
    ''', (chat_id,))
    conn.commit()
    conn.close()

def disable_chat_welcome(chat_id):
    """Выключить приветствия в чате"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO welcome_settings (chat_id, enabled)
        VALUES (?, 0)
        ON CONFLICT(chat_id) DO UPDATE SET enabled = 0
    ''', (chat_id,))
    conn.commit()
    conn.close()

def get_welcome_status(chat_id):
    """Статус приветствий для чата"""
    global_enabled = get_setting('global_welcome_enabled', '1') == '1'
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT enabled, message FROM welcome_settings WHERE chat_id = ?', (chat_id,))
    res = cursor.fetchone()
    
    if res:
        chat_enabled, message = res
        chat_enabled = bool(chat_enabled)
    else:
        chat_enabled, message = True, None
    
    conn.close()
    return {
        'global_enabled': global_enabled,
        'chat_enabled': chat_enabled,
        'message': message
    }

def set_global_welcome_status(enabled):
    """Установить глобальный статус"""
    set_setting('global_welcome_enabled', '1' if enabled else '0')

def get_welcome_settings_global():
    """Глобальный статус"""
    return get_setting('global_welcome_enabled', '1') == '1'

def get_welcome_chats_count():
    """Количество чатов с настроенными приветствиями"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM welcome_settings')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ========== СЕССИИ ==========

def save_user_selection(user_id, selection_data):
    """Сохранить выбор пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    chat_id = selection_data.get('chat_id')
    topic_id = selection_data.get('topic_id')
    uid = selection_data.get('user_id')
    period = selection_data.get('period', 'all_time')
    step = selection_data.get('step', 'select_chat')
    last = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO user_sessions (user_id, chat_id, topic_id, user_id_selected, period, step, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            chat_id = ?, topic_id = ?, user_id_selected = ?, period = ?, step = ?, last_updated = ?
    ''', (user_id, chat_id, topic_id, uid, period, step, last,
          chat_id, topic_id, uid, period, step, last))
    
    conn.commit()
    conn.close()

def get_user_selection(user_id):
    """Получить сохранённый выбор"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, topic_id, user_id_selected, period, step FROM user_sessions WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        return {
            'chat_id': res[0],
            'topic_id': res[1],
            'user_id': res[2],
            'period': res[3],
            'step': res[4]
        }
    return None

def clear_user_selection(user_id):
    """Очистить выбор"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ========== ОЧИСТКА ПОЛЬЗОВАТЕЛЯ ==========

def delete_user_stats(user_id, chat_id):
    """Удалить статистику пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def delete_user_from_all_topics(user_id, chat_id):
    """Удалить пользователя из всех тем"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_topics WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def delete_user_salary(user_id):
    """Удалить данные о зарплате"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM salary WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def delete_user_from_users_table(user_id, chat_id):
    """Удалить из таблицы users"""
    return delete_user_stats(user_id, chat_id)

def delete_user_complaints_data(user_id):
    """Удалить счётчик жалоб"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_complaints WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def delete_user_rewards(user_id):
    """Удалить награды"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM complaints_rewards WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

# ========== ЖАЛОБЫ И НАГРАДЫ ==========

def increment_complaint_count(user_id):
    """Увеличить счётчик жалоб"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO user_complaints (user_id, complaint_count, last_complaint_date)
        VALUES (?, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            complaint_count = complaint_count + 1,
            last_complaint_date = ?
    ''', (user_id, now, now))
    
    conn.commit()
    
    cursor.execute('SELECT complaint_count FROM user_complaints WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_complaint_count(user_id):
    """Количество жалоб"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT complaint_count FROM user_complaints WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def has_reward(user_id, reward_type):
    """Проверить наличие награды"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints_rewards WHERE user_id = ? AND reward_type = ?', (user_id, reward_type))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def add_reward(user_id, reward_type):
    """Добавить награду"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('INSERT INTO complaints_rewards (user_id, reward_type, achieved_date) VALUES (?, ?, ?)', (user_id, reward_type, now))
    conn.commit()
    conn.close()

def get_user_rewards(user_id):
    """Все награды пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT reward_type FROM complaints_rewards WHERE user_id = ? ORDER BY achieved_date', (user_id,))
    rewards = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rewards

# ========== ЛОГИРОВАНИЕ ==========

def log_auto_warn(user_id, user_name, has_media, has_text, count):
    """Логирование авто-варна в консоль"""
    media = "медиа" if has_media else ""
    text = "текст" if has_text else ""
    if media and text:
        warn_type = "медиа+текст"
    elif media:
        warn_type = "только медиа"
    elif text:
        warn_type = "только текст"
    else:
        warn_type = "пустое"
    
    print(f"⚠️ АВТО-ВАРН: {user_name} ({user_id}) - {warn_type} (всего: {count})")

# ========== ИНИЦИАЛИЗАЦИЯ ==========

if not os.path.exists(DB_PATH):
    init_database()
    print("🆕 Создана новая база данных")