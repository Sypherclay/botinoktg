"""
УПРАВЛЕНИЕ РАНГАМИ - ИСПРАВЛЕННАЯ ВЕРСИЯ
!хелпер, !модер, !куратор, !разжаловать и другие
"""
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
import traceback
from database import (
    set_user_rank_db, get_user_rank_db
)
from permissions import has_permission, is_owner, get_user_rank, get_clickable_name
from user_resolver import resolve_user
from constants import RANKS, OWNER_ID
from logger import log_rank_change, log_command

print("✅ rank.py загружен!")

async def handle_rank_command(update, context, rank_name):
    """Общая функция для всех рангов"""
    print(f"\n🔥 ВЫПОЛНЕНИЕ !{rank_name}")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        # Проверка прав
        if is_owner(user_id):
            pass
        else:
            admin_rank = get_user_rank(user_id)
            
            if admin_rank == 'curator' and rank_name in ['owner', 'curator']:
                rank_display = RANKS[rank_name]['name']
                await update.message.reply_text(f"❌ Куратор не может назначать ранг '{rank_display}'")
                return
            
            command_map = {
                'deputy_curator': '!зам',
                'manager': '!руководитель',
                'custom': '!кастом',
                'helper_plus': '!хелпер+'
            }
            command = command_map.get(rank_name, f'!{rank_name}')
            
            if not has_permission(user_id, command):
                await update.message.reply_text(f"❌ У вас нет прав назначать ранг '{RANKS[rank_name]['name']}'")
                return
        
        # Получаем цель из аргументов
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) < 2:
            await update.message.reply_text(
                f"❌ Укажите пользователя:\n"
                f"!{rank_name} @username\n"
                f"!{rank_name} ID\n"
                f"Или ответьте на сообщение",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Сохраняем аргументы для resolve_user
        context.args = parts[1:]
        
        user = await resolve_user(update, context)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        if user.id == OWNER_ID and rank_name != 'owner':
            await update.message.reply_text("❌ Нельзя изменить ранг владельца")
            return
        
        old_rank = get_user_rank_db(user.id)
        rank_display = RANKS[rank_name]['name']
        
        if set_user_rank_db(user.id, rank_name, user_id):
            admin_name = update.effective_user.full_name
            target_name = user.full_name or f"User {user.id}"
            
            log_rank_change(
                admin_id=user_id,
                admin_name=admin_name,
                user_id=user.id,
                user_name=target_name,
                old_rank=old_rank,
                new_rank=rank_name
            )
            
            clickable = get_clickable_name(user.id, user.first_name, user.username)
            await update.message.reply_text(
                f"✅ {clickable} назначен ранг '{rank_display}'",
                parse_mode=ParseMode.HTML
            )
            print(f"✅ Ранг назначен: {old_rank} -> {rank_name}")
        else:
            await update.message.reply_text("❌ Ошибка назначения ранга")
            
    except Exception as e:
        print(f"❌ Ошибка в handle_rank_command: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_demote(update, context):
    """!разжаловать - снять все ранги"""
    print("\n🔥 ВЫПОЛНЕНИЕ !разжаловать")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not has_permission(user_id, '!разжаловать'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        # Получаем цель из аргументов
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Укажите пользователя:\n"
                "!разжаловать @username\n"
                "!разжаловать ID\n"
                "Или ответьте на сообщение",
                parse_mode=ParseMode.HTML
            )
            return
        
        context.args = parts[1:]
        
        user = await resolve_user(update, context)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        if user.id == OWNER_ID:
            await update.message.reply_text("❌ Нельзя разжаловать владельца")
            return
        
        old_rank = get_user_rank_db(user.id)
        
        if old_rank == 'user':
            clickable = get_clickable_name(user.id, user.first_name, user.username)
            await update.message.reply_text(
                f"ℹ️ {clickable} уже имеет ранг 'Участник'",
                parse_mode=ParseMode.HTML
            )
            return
        
        if set_user_rank_db(user.id, 'user', user_id):
            admin_name = update.effective_user.full_name
            target_name = user.full_name or f"User {user.id}"
            
            log_rank_change(
                admin_id=user_id,
                admin_name=admin_name,
                user_id=user.id,
                user_name=target_name,
                old_rank=old_rank,
                new_rank='user'
            )
            
            clickable_admin = get_clickable_name(
                user_id,
                update.effective_user.first_name,
                update.effective_user.username
            )
            clickable_target = get_clickable_name(user.id, user.first_name, user.username)
            
            await update.message.reply_text(
                f"✅ {clickable_target} разжалован до 'Участник'\n"
                f"👑 Администратор: {clickable_admin}",
                parse_mode=ParseMode.HTML
            )
            print(f"✅ Пользователь разжалован: {old_rank} -> user")
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_demote: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд rank.py...")
    app.add_handler(MessageHandler(filters.Regex(r'^!хелпер\b'), lambda u,c: handle_rank_command(u,c,'helper')))
    app.add_handler(MessageHandler(filters.Regex(r'^!модер\b'), lambda u,c: handle_rank_command(u,c,'moder')))
    app.add_handler(MessageHandler(filters.Regex(r'^!руководитель\b'), lambda u,c: handle_rank_command(u,c,'manager')))
    app.add_handler(MessageHandler(filters.Regex(r'^!зам\b'), lambda u,c: handle_rank_command(u,c,'deputy_curator')))
    app.add_handler(MessageHandler(filters.Regex(r'^!куратор\b'), lambda u,c: handle_rank_command(u,c,'curator')))
    app.add_handler(MessageHandler(filters.Regex(r'^!владелец\b'), lambda u,c: handle_rank_command(u,c,'owner')))
    app.add_handler(MessageHandler(filters.Regex(r'^!кастом\b'), lambda u,c: handle_rank_command(u,c,'custom')))
    app.add_handler(MessageHandler(filters.Regex(r'^!хелпер\+\b'), lambda u,c: handle_rank_command(u,c,'helper_plus')))
    app.add_handler(MessageHandler(filters.Regex(r'^!разжаловать\b'), cmd_demote))
    print("✅ rank.py зарегистрирован")