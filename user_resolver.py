"""
user_resolver.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
from telegram import User
from database import (
    get_user_info, get_user_by_username, get_user_id_by_custom_nick,
    get_or_create_user
)
from constants import ANONYMOUS_ADMIN_ID
import traceback

OWNER_ID = None

def set_owner_id(owner_id):
    global OWNER_ID
    OWNER_ID = owner_id
    print(f"✅ user_resolver: OWNER_ID установлен {owner_id}")

async def resolve_user(update, context, required=True, allow_self=True, check_anon=True):
    """ЕДИНАЯ функция поиска пользователя"""
    print("\n🔍 resolve_user START")
    print(f"   required={required}, allow_self={allow_self}")
    
    user = None
    user_id = None
    message = update.message
    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    
    if not message:
        print("❌ Нет message")
        return None
    
    print(f"   Текст: {message.text}")
    
    # 1. REPLY
    if message.reply_to_message:
        reply_user = message.reply_to_message.from_user
        print(f"   REPLY: {reply_user.id} - {reply_user.first_name}")
        
        if check_anon and reply_user.id == ANONYMOUS_ADMIN_ID:
            print(f"   ⚠️ Анонимный админ - игнорируем")
        elif check_anon and OWNER_ID and reply_user.id == OWNER_ID:
            print(f"   ⚠️ Владелец - игнорируем")
        else:
            user = reply_user
            user_id = user.id
            print(f"   ✅ Взят из reply")
    
    # 2. АРГУМЕНТЫ
    if not user and context.args:
        target = context.args[0]
        print(f"   АРГУМЕНТ: {target}")
        
        try:
            user_id = int(target)
            print(f"      Это ID: {user_id}")
            
            user_info = get_user_info(user_id, chat_id) if chat_id else None
            if user_info:
                user_name, username = user_info
                # ✅ ВАЖНО: создаём объект User!
                user = User(id=user_id, first_name=user_name, username=username, is_bot=False)
                print(f"      ✅ Найден в БД: {user_name}")
            else:
                try:
                    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
                    if chat_member and chat_member.user:
                        user = chat_member.user
                        print(f"      ✅ Найден через API: {user.first_name}")
                except Exception as e:
                    print(f"      ❌ Ошибка API: {e}")
                    # ✅ Создаём минимальный объект User
                    user = User(id=user_id, first_name=f"User {user_id}", is_bot=False)
                    
        except ValueError:
            if target.startswith('@'):
                clean_target = target[1:]
                print(f"      Это username: @{clean_target}")
                
                user_data = get_user_by_username(clean_target, chat_id) if chat_id else None
                if user_data:
                    user_id, user_name = user_data
                    # ✅ ВАЖНО: создаём объект User!
                    user = User(id=user_id, first_name=user_name, username=clean_target, is_bot=False)
                    print(f"      ✅ Найден в БД: {user_name}")
                else:
                    try:
                        chat = await context.bot.get_chat(f"@{clean_target}")
                        if chat and not chat.is_bot:
                            user = chat
                            user_id = chat.id
                            print(f"      ✅ Найден через API: {user.first_name}")
                    except Exception as e:
                        print(f"      ❌ Ошибка API: {e}")
            else:
                print(f"      Это кастомный ник: {target}")
                user_id_from_nick = get_user_id_by_custom_nick(target)
                if user_id_from_nick:
                    user_info = get_user_info(user_id_from_nick, chat_id) if chat_id else None
                    if user_info:
                        user_name, username = user_info
                        # ✅ ВАЖНО: создаём объект User!
                        user = User(id=user_id_from_nick, first_name=user_name, username=username, is_bot=False)
                        user_id = user_id_from_nick
                        print(f"      ✅ Найден по кастомному нику: {user_name}")
    
    # 3. СЕБЯ
    if not user and allow_self:
        user = update.effective_user
        user_id = user.id
        print(f"   СЕБЯ: {user_id}")
    
    # РЕЗУЛЬТАТ
    if not user and required:
        print(f"   ❌ Пользователь не найден!")
        await message.reply_text(
            "❌ Укажите пользователя:\n"
            "1. Ответьте на сообщение\n"
            "2. @username\n"
            "3. ID\n"
            "4. Кастомный ник",
            parse_mode='HTML'
        )
        return None
    
    if user:
        print(f"   ✅ ИТОГ: {user.first_name} (ID: {user.id})")
    print("🔍 resolve_user END\n")
    
    return user  # ⬅️ ВАЖНО: возвращаем ТОЛЬКО user, не tuple!