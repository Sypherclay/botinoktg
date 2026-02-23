"""
ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
"""

def check_milestones(user_id, chat_id, topic_id, message_count):
    """Проверка достижения юбилейных отметок"""
    from database import (
        get_milestone_tracked_topics, get_user_achieved_milestones,
        add_user_milestone, get_user_custom_nick, get_milestone_message,
        get_user_info
    )
    
    tracked_topics = get_milestone_tracked_topics()
    if str(topic_id) not in tracked_topics:
        return None
    
    achieved = get_user_achieved_milestones(user_id, chat_id)
    milestones = [500, 1000, 1500, 2000, 2500, 3000]
    
    for milestone in milestones:
        if message_count >= milestone and milestone not in achieved:
            add_user_milestone(user_id, chat_id, milestone)
            
            custom_nick = get_user_custom_nick(user_id)
            if custom_nick:
                user_display_name = custom_nick
            else:
                user_info = get_user_info(user_id, chat_id)
                if user_info:
                    user_display_name = user_info[0]
                else:
                    user_display_name = f"Пользователь {user_id}"
            
            message_template = get_milestone_message(milestone)
            if message_template:
                congrat_message = message_template.format(ник=user_display_name)
                return congrat_message
    
    return None

def get_user_vacation_info(user_id):
    """Получить информацию об отпуске пользователя"""
    from database import get_user_vacation_info_db
    return get_user_vacation_info_db(user_id)

def format_number(num):
    """Форматировать число с разделителями тысяч"""
    return f"{num:,}".replace(",", " ")

def get_progress_bar(current, maximum, length=10):
    """Создать прогресс-бар"""
    if maximum <= 0:
        return "░" * length
    
    filled = int((current / maximum) * length)
    filled = min(filled, length)
    
    return "█" * filled + "░" * (length - filled)

def parse_date(date_str):
    """Распарсить дату из строки"""
    from datetime import datetime
    formats = [
        "%d.%m.%Y",
        "%d.%m.%y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d/%m/%y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def escape_html(text):
    """Экранировать HTML специальные символы"""
    if not text:
        return text
    
    replacements = [
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ('"', "&quot;"),
    ]
    
    for old, new in replacements:
        text = text.replace(old, new)
    
    return text

def truncate(text, length=100, suffix="..."):
    """Обрезать текст до указанной длины"""
    if not text or len(text) <= length:
        return text
    
    return text[:length].rsplit(' ', 1)[0] + suffix