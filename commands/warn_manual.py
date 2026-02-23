"""
РУЧНЫЕ ВАРНЫ - ПОЛНАЯ ВЕРСИЯ
!варн - только для Куратор+ (выдать варн)
!снять варн - только для Куратор+ (снять последний варн)
!варн лист - только для Руководитель+ (список всех)
"""
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
import traceback
from database import (
    add_warning_v2, get_user_warns_with_reasons, get_all_users_with_warns,
    remove_last_warn, get_user_rank_db, get_user_info
)
from permissions import has_permission, get_clickable_name, get_user_rank
from user_resolver import resolve_user
from constants import RANKS, ANONYMOUS_ADMIN_ID
from logger import log_command

print("✅ warn_manual.py загружен (полная версия с рангами)!")

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПРОВЕРКИ РАНГА ==========
def has_rank(user_id, required_rank):
    """Проверяет, имеет ли пользователь требуемый ранг или выше"""
    user_rank = get_user_rank_db(user_id)
    
    # Список рангов по возрастанию
    rank_levels = {
        'user': 0,
        'helper': 1,
        'helper_plus': 2,
        'custom': 3,
        'moder': 4,
        'manager': 5,
        'deputy_curator': 6,
        'curator': 7,
        'owner': 8
    }
    
    user_level = rank_levels.get(user_rank, 0)
    required_level = rank_levels.get(required_rank, 0)
    
    return user_level >= required_level

async def cmd_add_warn(update, context):
    """!варн [причина] - выдать ручной варн (только для Куратор+)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !варн")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        # ✅ ПРОВЕРКА: только для Куратор и выше
        if not has_rank(user_id, 'curator'):
            user_rank = get_user_rank_db(user_id)
            rank_name = RANKS.get(user_rank, {}).get('name', 'Участник')
            await update.message.reply_text(
                f"❌ У вас нет прав для этой команды.\n"
                f"Требуется ранг: Куратор или выше\n"
                f"Ваш ранг: {rank_name}",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Получаем полный текст сообщения
        message_text = update.message.text or ""
        lines = message_text.strip().split('\n', 1)
        first_line = lines[0].strip()
        parts = first_line.split(maxsplit=1)
        
        # Определяем причину
        reason = "Без причины"
        
        # Если есть вторая строка - это причина (приоритет)
        if len(lines) > 1:
            reason = lines[1].strip()
        # Если нет второй строки, но есть аргументы в первой строке
        elif len(parts) > 1:
            reason = parts[1].strip()
        
        print(f"   причина: {reason}")
        
        # Сохраняем аргументы для resolve_user (если есть)
        if len(parts) > 1 and not parts[1].startswith(('@', '!')) and not parts[1].isdigit():
            # Если первый аргумент не похож на пользователя - это часть причины
            context.args = []
        else:
            context.args = parts[1:] if len(parts) > 1 else []
        
        # Ищем пользователя (приоритет: reply > аргументы)
        user = await resolve_user(update, context, required=True, allow_self=False)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        # Проверка на анонимного админа
        if user.id == ANONYMOUS_ADMIN_ID:
            await update.message.reply_text("❌ Нельзя выдать варн анонимному администратору")
            return
        
        # Проверка ранга цели (нельзя выдавать варны кураторам и выше)
        target_rank = get_user_rank_db(user.id)
        if target_rank in ['curator', 'owner', 'deputy_curator']:
            rank_name = RANKS.get(target_rank, {}).get('name', '')
            await update.message.reply_text(f"❌ Нельзя выдать варн пользователю с рангом '{rank_name}'")
            return
        
        # Добавляем варн с причиной
        total_warns = add_warning_v2(
            user.id, chat_id, reason,
            user_id, update.effective_user.full_name,
            warn_type="ручной"
        )
        
        admin_name = update.effective_user.full_name
        
        # Получаем кликабельное имя цели
        clickable_target = get_clickable_name(user.id, user.first_name, user.username)
        
        # Отправляем подтверждение
        await update.message.reply_text(
            f"⚠️ {clickable_target} получил варн\n"
            f"📝 Причина: {reason}\n"
            f"👮 Выдал: {admin_name}\n"
            f"📊 Всего варнов: {total_warns}",
            parse_mode=ParseMode.HTML
        )
        
        log_command(
            "!варн", user_id, admin_name,
            chat_id, f"Цель: {user.id}, Причина: {reason}"
        )
        
        print(f"✅ Варн выдан, всего варнов: {total_warns}")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_add_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_remove_warn(update, context):
    """!снять варн - снять ПОСЛЕДНИЙ варн (только для Куратор+)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !снять варн")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        # ✅ ПРОВЕРКА: только для Куратор и выше
        if not has_rank(user_id, 'curator'):
            user_rank = get_user_rank_db(user_id)
            rank_name = RANKS.get(user_rank, {}).get('name', 'Участник')
            await update.message.reply_text(
                f"❌ У вас нет прав для этой команды.\n"
                f"Требуется ранг: Куратор или выше\n"
                f"Ваш ранг: {rank_name}",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Получаем текст сообщения
        message_text = update.message.text
        parts = message_text.split()
        
        # Сохраняем аргументы для resolve_user
        if len(parts) > 1:
            context.args = parts[1:]
        
        # Ищем пользователя
        user = await resolve_user(update, context, required=True, allow_self=False)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
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
        
        # Получаем оставшиеся варны
        remaining = get_user_warns_with_reasons(user.id, chat_id, active_only=True)
        remaining_count = len(remaining)
        
        clickable_target = get_clickable_name(user.id, user.first_name, user.username)
        admin_name = update.effective_user.full_name
        
        # Извлекаем причину без метки [ручной]
        clean_reason = removed_reason.replace('[ручной] ', '') if '[ручной]' in removed_reason else removed_reason
        
        await update.message.reply_text(
            f"✅ {clickable_target} снят последний варн\n"
            f"📝 Причина варна: {clean_reason}\n"
            f"👮 Снял: {admin_name}\n"
            f"📊 Осталось варнов: {remaining_count}",
            parse_mode=ParseMode.HTML
        )
        print(f"✅ Варн снят, осталось: {remaining_count}")
        
        log_command(
            "!снять варн", user_id, admin_name,
            chat_id, f"Цель: {user.id}, Снят варн: {clean_reason}"
        )
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_remove_warn: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_warn_list(update, context):
    """!варн лист - список всех пользователей с варнами (только для Руководитель+)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !варн лист")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   user_id: {user_id}")
        
        # ✅ ПРОВЕРКА: только для Руководитель и выше
        if not has_rank(user_id, 'manager'):
            user_rank = get_user_rank_db(user_id)
            rank_name = RANKS.get(user_rank, {}).get('name', 'Участник')
            await update.message.reply_text(
                f"❌ У вас нет прав для этой команды.\n"
                f"Требуется ранг: Руководитель или выше\n"
                f"Ваш ранг: {rank_name}",
                parse_mode=ParseMode.HTML
            )
            return
        
        print(f"   ✅ Права есть: ранг {get_user_rank_db(user_id)}")
        
        # Получаем всех пользователей с варнами
        users_with_warns = get_all_users_with_warns(chat_id)
        
        if not users_with_warns:
            await update.message.reply_text("📭 Нет пользователей с активными варнами")
            return
        
        # Группируем по пользователям
        warns_by_user = {}
        for uid, name, username, reason, date, warned_by in users_with_warns:
            if uid not in warns_by_user:
                warns_by_user[uid] = {
                    'name': name or f"User {uid}",
                    'username': username,
                    'warns': []
                }
            
            # Очищаем причину от метки [ручной]
            clean_reason = reason.replace('[ручной] ', '') if '[ручной]' in reason else reason
            
            warns_by_user[uid]['warns'].append({
                'reason': clean_reason,
                'date': date,
                'warned_by': warned_by
            })
        
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
        
        # Если ответ слишком длинный, разбиваем на части
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for i, part in enumerate(parts, 1):
                if i == 1:
                    await update.message.reply_text(part, parse_mode=ParseMode.HTML)
                else:
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
    app.add_handler(MessageHandler(filters.Regex(r'^!варн\b'), cmd_add_warn))
    app.add_handler(MessageHandler(filters.Regex(r'^!снять варн\b'), cmd_remove_warn))
    # ⚠️ ВАЖНО: именно "!варн лист" с пробелом!
    app.add_handler(MessageHandler(filters.Regex(r'^!варн лист\b'), cmd_warn_list))
    print("✅ warn_manual.py зарегистрирован")