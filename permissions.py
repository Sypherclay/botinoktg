"""
permissions.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
from database import (
    is_admin_db, get_user_rank_db, set_user_rank_db,
    get_user_custom_nick, get_user_info
)
from constants import RANKS, OWNER_ID

def is_admin(user_id):
    return is_admin_db(user_id)

def is_owner(user_id):
    return user_id == OWNER_ID

def get_user_rank(user_id):
    return get_user_rank_db(user_id)

def set_user_rank(user_id, rank):
    return set_user_rank_db(user_id, rank)

def has_permission(user_id, command):
    rank = get_user_rank(user_id)
    rank_info = RANKS.get(rank, RANKS['user'])
    
    if user_id == OWNER_ID:
        return True
    
    if command in rank_info['commands']:
        return True
    
    user_level = rank_info['level']
    for rank_name, rank_data in RANKS.items():
        if command in rank_data['commands']:
            if user_level >= rank_data['level']:
                return True
            else:
                return False
    
    return False

def get_user_display_name(user_id, user_name="", username=""):
    custom_nick = get_user_custom_nick(user_id)
    
    if custom_nick:
        return custom_nick
    elif user_name:
        return user_name
    else:
        user_info = get_user_info(user_id, '0')
        if user_info and user_info[0]:
            return user_info[0]
        return f"User {user_id}"

def get_clickable_name(user_id, display_name=None, username=None):
    """СОЗДАЕТ КЛИКАБЕЛЬНУЮ ССЫЛКУ НА ПОЛЬЗОВАТЕЛЯ"""
    user_id_int = user_id if isinstance(user_id, int) else int(user_id)
    
    # Получаем кастомный ник
    custom_nick = get_user_custom_nick(user_id_int)
    
    # Определяем текст для отображения
    display_text = ""
    
    if custom_nick:
        display_text = custom_nick
    elif username:
        display_text = f"@{username}"
    elif display_name:
        display_text = display_name
    else:
        user_info = get_user_info(user_id_int, '0')
        if user_info and user_info[0]:
            display_text = user_info[0]
        else:
            display_text = f"User {user_id_int}"
    
    # ✅ Проверка на None и пустые значения
    if display_text is None:
        display_text = f"User {user_id_int}"
    
    # Обрезаем длинные имена (только если это строка)
    if isinstance(display_text, str) and len(display_text) > 50:
        display_text = display_text[:47] + "..."
    
    # Всегда оборачиваем в HTML-ссылку
    return f'<a href="tg://user?id={user_id_int}">{display_text}</a>'

def get_user_clickable_info(user_id, user_name="", username=""):
    return get_clickable_name(user_id, user_name, username)

def is_admin_or_owner(user_id):
    return is_admin(user_id) or is_owner(user_id)

def get_user_level(user_id):
    rank = get_user_rank(user_id)
    return RANKS.get(rank, RANKS['user'])['level']