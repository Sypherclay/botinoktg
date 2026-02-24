"""
РУЧНЫЕ ВАРНЫ - РАБОЧАЯ ВЕРСИЯ
!варн - выдаёт варн (поддерживает @user, ID, reply и причину на след. строке)
!снять варн - снимает последний варн (поддерживает @user, ID, reply)
!варн лист - список всех пользователей с варнами
"""
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
import traceback
from database import (
    add_warning_v2, get_user_warns_with_reasons, get_all_users_with_warns,
    remove_last_warn, get_user_rank_db, get_user_info
)
from permissions import has_permission, get_clickable_name, get_user_rank, is_owner
from user_resolver import resolve_user
from constants import RANKS, ANONYMOUS_ADMIN_ID
from logger import log_command

print("✅ warn_manual.py загружен (рабочая версия)!")

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПРОВЕРКИ РАНГА ==========
def has_rank(user_id, required_rank):
    """Проверяет, имеет ли пользователь требуемый ранг или выше"""
    if is_owner(user_id):
        return True
    
    user_rank = get_user_rank_db(user_id)
    
    rank_levels = {
        'user': 0, 'helper': 1, 'helper_plus': 2, 'custom': 3,
        'moder': 4, 'manager': 5, 'deputy_curator': 6, 'curator': 7, 'owner': 8
    }
    
    return rank_levels.get(user_rank, 0) >= rank_levels.get(required_rank, 0)

async def cmd_add_warn(update, context):
    """!варн [причина] - выдать ручной варн"""
    print("\n🔥 ВЫПОЛНЕНИЕ !варн")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not has_rank(user_id, 'curator'):
            user_rank = get_user_rank_db(user_id)
            rank_name = RANKS.get(user_rank, {}).get('name', 'Участник')
            await update.message.reply_text(
                f"❌ У вас нет прав для этой команды.\nТребуется ранг: Куратор или выше\nВаш ранг: {rank_name}",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Получаем полный текст сообщения
        message_text = update.message.text or ""
        lines = message_text.strip().split('\n', 1)
        first_line = lines[0].strip()
        
        # Разбираем первую строку на команду и возможный аргумент
        parts = first_line.split(maxsplit=1)
        
        # По умолчанию причина пустая
        reason = "Без причины"
        target_arg = None
        
        # Если есть аргумент в первой строке
        if len(parts) > 1:
            target_arg = parts[1]
            print(f"   возможный аргумент: {target_arg}")
        
        # Если есть вторая строка - это причина
        if len(lines) > 1:
            reason = lines[1].strip()
            print(f"   причина из второй строки: {reason}")
        
        # Определяем, нужно ли искать пользователя
        user = None
        
        # 1. Сначала проверяем reply
        if update.message.reply_to_message:
            user = update.message.reply_to_message.from_user
            print(f"   найден по reply: {user.id}")
            # Если есть аргумент, но это не похоже на пользователя - это может быть причина
            if target_arg and not target_arg.startswith('@') and not target_arg.isdigit():
                reason = target_arg
        
        # 2. Если нет reply, но есть аргумент
        elif target_arg:
            # Проверяем, похож ли аргумент на пользователя
            if target_arg.startswith('@') or target_arg.isdigit():
                # Это похоже на пользователя
                context.args = [target_arg]
                user = await resolve_user(update, context, required=True, allow_self=False)
                if not user:
                    return
                print(f"   найден по аргументу: {user.id}")
            else:
                # Аргумент - это часть причины
                reason = target_arg + (" " + reason if reason != "Без причины" else "")
                # Берём себя? Нет, нельзя выдать варн себе
                await update.message.reply_text(
                    "❌ Укажите пользователя:\n1. Ответьте на сообщение\n2. @username\n3. ID",
                    parse_mode=ParseMode.HTML
                )
                return
        
        # 3. Если нет ни reply, ни аргумента
        else:
            await update.message.reply_text(
                "❌ Укажите пользователя:\n1. Ответьте на сообщение\n2. @username\n3. ID",
                parse_mode=ParseMode.HTML
            )
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        print(f"   причина: {reason}")
        
        # Проверка на анонимного админа
        if user.id == ANONYMOUS_ADMIN_ID:
            await update.message.reply_text("❌ Нельзя выдать варн анонимному администратору")
            return
        
        # Проверка ранга цели
        if not is_owner(user_id):
            target_rank = get_user_rank_db(user.id)
            if target_rank in ['curator', 'owner', 'deputy_curator']:
                rank_name = RANKS.get(target_rank, {}).get('name', '')
                await update.message.reply_text(f"❌ Нельзя выдать варн пользователю с рангом '{rank_name}'")
                return
        
        # Добавляем варн
        total_warns = add_warning_v2(
            user.id, chat_id, reason,
            user_id, update.effective_user.full_name,
            warn_type="ручной"
        )
        
        admin_name = update.effective_user.full_name
        clickable_target = get_clickable_name(user.id, user.first_name, user.username)
        
        await update.message.reply_text(
            f"⚠️ {clickable_target} получил варн\n📝 Причина: {reason}\n👮 Выдал: {admin_name}\n📊 Всего варнов: {total_warns}",
            parse_mode=ParseMode.HTML
        )
        
        log_command("!варн", user_id, admin_name, chat_id, f"Цель: {user.id}, Причина: {reason}")
        print(f"✅ Варн выдан, всего варнов: {total_warns}")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_add_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_remove_warn(update, context):
    """!снять варн - снять последний варн"""
    print("\n🔥 ВЫПОЛНЕНИЕ !снять варн")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not has_rank(user_id, 'curator'):
            user_rank = get_user_rank_db(user_id)
            rank_name = RANKS.get(user_rank, {}).get('name', 'Участник')
            await update.message.reply_text(
                f"❌ У вас нет прав для этой команды.\nТребуется ранг: Куратор или выше\nВаш ранг: {rank_name}",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Получаем текст сообщения
        message_text = update.message.text
        parts = message_text.split(maxsplit=1)
        
        # Ищем пользователя
        user = None
        
        # 1. Сначала проверяем reply
        if update.message.reply_to_message:
            user = update.message.reply_to_message.from_user
            print(f"   найден по reply: {user.id}")
        
        # 2. Если нет reply, но есть аргумент
        elif len(parts) > 1:
            context.args = [parts[1]]
            print(f"   аргумент для поиска: {context.args}")
            user = await resolve_user(update, context, required=True, allow_self=False)
            if not user:
                return
            print(f"   найден по аргументу: {user.id}")
        
        # 3. Если нет ничего
        else:
            await update.message.reply_text(
                "❌ Укажите пользователя:\n1. Ответьте на сообщение\n2. @username\n3. ID",
                parse_mode=ParseMode.HTML
            )
            return
        
        if user.id == ANONYMOUS_ADMIN_ID:
            await update.message.reply_text("❌ Нельзя снять варн анонимному администратору")
            return
        
        # Снимаем последний варн
        removed_reason = remove_last_warn(
            user.id, chat_id,
            user_id, update.effective_user.full_name
        )
        
        if not removed_reason:
            await update.message.reply_text(f"ℹ️ У пользователя нет активных варнов")
            return
        
        remaining = get_user_warns_with_reasons(user.id, chat_id, active_only=True)
        remaining_count = len(remaining)
        
        clickable_target = get_clickable_name(user.id, user.first_name, user.username)
        admin_name = update.effective_user.full_name
        
        clean_reason = removed_reason.replace('[ручной] ', '') if '[ручной]' in removed_reason else removed_reason
        
        await update.message.reply_text(
            f"✅ {clickable_target} снят последний варн\n📝 Причина варна: {clean_reason}\n👮 Снял: {admin_name}\n📊 Осталось варнов: {remaining_count}",
            parse_mode=ParseMode.HTML
        )
        print(f"✅ Варн снят, осталось: {remaining_count}")
        
        log_command("!снять варн", user_id, admin_name, chat_id, f"Цель: {user.id}")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_remove_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_warn_list(update, context):
    """!варн лист - список всех пользователей с варнами"""
    print("\n🔥 ВЫПОЛНЕНИЕ !варн лист")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        if not has_rank(user_id, 'manager'):
            user_rank = get_user_rank_db(user_id)
            rank_name = RANKS.get(user_rank, {}).get('name', 'Участник')
            await update.message.reply_text(
                f"❌ У вас нет прав для этой команды.\nТребуется ранг: Руководитель или выше\nВаш ранг: {rank_name}",
                parse_mode=ParseMode.HTML
            )
            return
        
        users_with_warns = get_all_users_with_warns(chat_id)
        
        if not users_with_warns:
            await update.message.reply_text("📭 Нет пользователей с активными варнами")
            return
        
        warns_by_user = {}
        for uid, name, username, reason, date, warned_by in users_with_warns:
            if uid not in warns_by_user:
                warns_by_user[uid] = {'name': name or f"User {uid}", 'username': username, 'warns': []}
            
            clean_reason = reason.replace('[ручной] ', '') if '[ручной]' in reason else reason
            warns_by_user[uid]['warns'].append({'reason': clean_reason, 'date': date, 'warned_by': warned_by})
        
        lines = ["📋 <b>СПИСОК АКТИВНЫХ ВАРНОВ</b>", "="*35]
        lines.append(f"👥 Всего пользователей: {len(warns_by_user)}")
        lines.append("="*35 + "\n")
        
        for uid, data in warns_by_user.items():
            clickable = get_clickable_name(uid, data['name'], data['username'] or "")
            lines.append(f"👤 {clickable}")
            lines.append(f"   ⚠️ Варнов: {len(data['warns'])}")
            
            for i, warn in enumerate(data['warns'], 1):
                from datetime import datetime
                date_str = datetime.fromisoformat(warn['date']).strftime("%d.%m.%Y %H:%M")
                lines.append(f"      {i}. {warn['reason'][:50]}")
                lines.append(f"         👮 {warn['warned_by']} | {date_str}")
            lines.append("")
        
        response = "\n".join(lines)
        
        if len(response) > 4000:
            for i, part in enumerate([response[i:i+4000] for i in range(0, len(response), 4000)], 1):
                await update.message.reply_text(part, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
        print("✅ Список варнов отправлен")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_warn_list: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд warn_manual.py...")
    app.add_handler(MessageHandler(filters.Regex(r'^!варн лист\b'), cmd_warn_list))
    app.add_handler(MessageHandler(filters.Regex(r'^!варн\b'), cmd_add_warn))
    app.add_handler(MessageHandler(filters.Regex(r'^!снять варн\b'), cmd_remove_warn))
    print("✅ warn_manual.py зарегистрирован")