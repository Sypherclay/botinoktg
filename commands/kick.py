"""
КИКИ И РАЗБАН
!убрать, !вернуть
"""
from telegram.ext import MessageHandler, filters, CommandHandler
from telegram.constants import ParseMode
from database import (
    remove_all_warnings, get_warnings_count, get_kick_topic_id,
    get_user_info
)
from permissions import has_permission, get_clickable_name
from user_resolver import resolve_user
from constants import ANONYMOUS_ADMIN_ID, OWNER_ID
from logger import log_kick, log_command, log_admin_action, log_error

async def cmd_kick(update, context):
    """!убрать [причина] - исключить пользователя"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    chat_id_int = update.effective_chat.id
    
    if not has_permission(user_id, '!убрать'):
        await update.message.reply_text("❌ Нет прав")
        return
    
    reason = "Нарушение правил"
    user = await resolve_user(update, context)
    if not user:
        return
    
    if context.args and not update.message.reply_to_message:
        reason = ' '.join(context.args)
    elif len(context.args) > 1:
        reason = ' '.join(context.args[1:])
    
    if user.id in [ANONYMOUS_ADMIN_ID, OWNER_ID] or (user.username == 'GroupAnonymousBot' and user.id not in [1328519402, 7266756475]):
        await update.message.reply_text("❌ Нельзя исключить этого пользователя")
        return
    
    if user.is_bot and user.id not in [1328519402, 7266756475]:
        await update.message.reply_text("❌ Нельзя исключить бота")
        return
    
    warnings_before = get_warnings_count(user.id, chat_id)
    clickable = get_clickable_name(user.id, user.first_name, user.username)
    
    try:
        is_admin_before = False
        try:
            member = await context.bot.get_chat_member(chat_id_int, user.id)
            is_admin_before = member.status in ['administrator', 'creator']
        except:
            pass
        
        await context.bot.ban_chat_member(
            chat_id=chat_id_int,
            user_id=user.id,
            revoke_messages=True
        )
        
        if is_admin_before:
            reason += " (бывший администратор)"
        
        admin_name = update.effective_user.full_name
        remove_all_warnings(user.id, chat_id, user_id, admin_name, reason)
        
        topic = get_kick_topic_id()
        if topic:
            try:
                msg = f"{clickable} Снят.\nПричина: {reason}\nВыговоров было: {warnings_before}/3"
                await context.bot.send_message(
                    chat_id=chat_id_int,
                    message_thread_id=int(topic),
                    text=msg,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                log_error("KICK_TOPIC", str(e))
        
        log_kick(
            user_id=user.id,
            user_name=user.full_name,
            reason=reason,
            by_admin=admin_name
        )
        
        log_command(
            "!убрать", user_id, admin_name,
            chat_id, f"Цель: {user.id}, Причина: {reason}"
        )
        
        await update.message.reply_text(
            f"🚫 {clickable} исключён.",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        log_error("KICK_ERROR", str(e), user_id, chat_id_int)
        
        error = "❌ Не удалось исключить.\n"
        if "not enough rights" in str(e).lower():
            error += "У бота недостаточно прав.\nПроверьте:\n• Бот должен быть администратором\n• Право 'Блокировка пользователей'\n• Право 'Удаление сообщений'"
        elif "user is an administrator" in str(e).lower():
            error += "Пользователь является администратором.\nСначала снимите права вручную."
        else:
            error += f"Ошибка: {str(e)[:100]}"
        
        await update.message.reply_text(error, parse_mode=ParseMode.HTML)

async def cmd_unban(update, context):
    """!вернуть @username/ID - разбанить пользователя"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    chat_id_int = update.effective_chat.id
    
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ Работает только в группах")
        return
    
    if not has_permission(user_id, '!вернуть'):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("!вернуть @username\n!вернуть ID")
        return
    
    target = context.args[0]
    target_id = None
    
    try:
        target_id = int(target)
    except ValueError:
        if target.startswith('@'):
            clean = target[1:]
            try:
                chat = await context.bot.get_chat(f"@{clean}")
                if chat:
                    target_id = chat.id
            except:
                pass
    
    if not target_id:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    try:
        await context.bot.unban_chat_member(
            chat_id=chat_id_int,
            user_id=target_id
        )
        
        info = get_user_info(target_id, chat_id)
        if info:
            name, username = info
        else:
            name, username = f"User {target_id}", ""
        
        clickable_user = get_clickable_name(target_id, name, username)
        clickable_admin = get_clickable_name(
            user_id,
            update.effective_user.first_name,
            update.effective_user.username
        )
        
        log_admin_action(
            admin_id=user_id,
            admin_name=update.effective_user.full_name,
            action="Разбанил",
            target=f"{target_id} (@{username})"
        )
        
        await update.message.reply_text(
            f"✅ {clickable_admin} вернул {clickable_user}",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        log_error("UNBAN_ERROR", str(e), user_id, chat_id_int)
        
        error = "❌ Не удалось разбанить.\n"
        if "not enough rights" in str(e).lower():
            error += "У бота недостаточно прав."
        elif "user not found" in str(e).lower():
            error += "Пользователь не найден в бане."
        else:
            error += f"Ошибка: {str(e)[:100]}"
        
        await update.message.reply_text(error, parse_mode=ParseMode.HTML)

async def kick_user(update, context, user, reason):
    """Автоматический кик пользователя"""
    chat_id_int = update.effective_chat.id
    chat_id = str(chat_id_int)
    
    clickable = get_clickable_name(user.id, user.first_name, user.username)
    warnings_before = get_warnings_count(user.id, chat_id)
    
    try:
        await context.bot.ban_chat_member(
            chat_id=chat_id_int,
            user_id=user.id,
            revoke_messages=True
        )
        
        await context.bot.unban_chat_member(
            chat_id=chat_id_int,
            user_id=user.id
        )
        
        remove_all_warnings(user.id, chat_id, 0, 'Авто-система', 'Сняты при авто-кике')
        
        topic = get_kick_topic_id()
        if topic:
            try:
                msg = f"{clickable} Снят.\nПричина: {reason}"
                await context.bot.send_message(
                    chat_id=chat_id_int,
                    message_thread_id=int(topic),
                    text=msg,
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
        
        log_kick(
            user_id=user.id,
            user_name=user.full_name,
            reason=reason,
            by_admin="Система"
        )
        
        await update.message.reply_text(
            f"🚫 {clickable} Снят за {reason}",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        log_error("AUTO_KICK_ERROR", str(e), user.id, chat_id_int)
        await update.message.reply_text(
            f"❌ Не удалось исключить. Убедитесь, что бот - администратор."
        )

def register(app):
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!убрать\b'), cmd_kick))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!вернуть\b'), cmd_unban))