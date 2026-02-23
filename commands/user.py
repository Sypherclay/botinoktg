"""
УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
!ник, !очистить, !adduser
"""
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram import User
from database import (
    get_user_custom_nick, set_user_custom_nick,
    get_user_id_by_custom_nick, get_user_info,
    delete_user_warnings, delete_user_rank, delete_user_vacation,
    delete_user_auto_warn_count, delete_user_milestones,
    delete_user_from_all_topics, delete_user_from_users_table,
    delete_user_salary, delete_user_complaints_data, delete_user_rewards,
    get_or_create_user, get_or_create_topic, add_user_to_topic,
    user_exists_in_chat, add_chat_to_db, get_all_chats
)
from permissions import has_permission, is_admin, get_clickable_name
from user_resolver import resolve_user
from constants import OWNER_ID
from logger import log_admin_action, log_user_action

async def cmd_nick(update, context):
    user_id = update.effective_user.id
    
    if not context.args:
        current = get_user_custom_nick(user_id)
        if current:
            await update.message.reply_text(f"ℹ️ Ваш ник: {current}\n!ник НовыйНик")
        else:
            await update.message.reply_text("!ник ВашНик")
        return
    
    nick = ' '.join(context.args).strip()
    if len(nick) > 50:
        await update.message.reply_text("❌ Слишком длинный (макс. 50)")
        return
    
    set_user_custom_nick(user_id, nick)
    clickable = get_clickable_name(user_id, update.effective_user.first_name, update.effective_user.username)
    await update.message.reply_text(f"✅ Ваш ник установлен: {nick}\n👤 Теперь вы: {clickable}", parse_mode=ParseMode.HTML)
    log_user_action(user_id, update.effective_user.full_name, "Установил ник", nick)

async def cmd_clear_user(update, context):
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not has_permission(user_id, '!очистить'):
        await update.message.reply_text("❌ Нет прав")
        return
    
    user = await resolve_user(update, context)
    if not user:
        return
    
    removed = {
        'warnings': delete_user_warnings(user.id, chat_id),
        'rank': delete_user_rank(user.id) if user.id != OWNER_ID else False,
        'vacation': delete_user_vacation(user.id),
        'auto_warn': delete_user_auto_warn_count(user.id),
        'salary': delete_user_salary(user.id),
        'milestones': delete_user_milestones(user.id, chat_id),
        'topics': delete_user_from_all_topics(user.id, chat_id),
        'user': delete_user_from_users_table(user.id, chat_id),
        'complaints': delete_user_complaints_data(user.id),
        'rewards': delete_user_rewards(user.id)
    }
    
    clickable = get_clickable_name(user.id, user.first_name, user.username)
    response = f"✅ {clickable} полностью очищен:\n\n"
    response += f"• Выговоры: удалено {removed['warnings']}\n"
    response += f"• Ранг: {'сброшен' if removed['rank'] else 'не изменён'}\n"
    response += f"• Отпуски: {'удалены' if removed['vacation'] else 'не найдены'}\n"
    response += f"• Авто-варны: {'обнулены' if removed['auto_warn'] else 'не найдены'}\n"
    response += f"• Зарплата: {'сброшена' if removed['salary'] else 'не найдена'}\n"
    response += f"• Юбилеи: {'очищены' if removed['milestones'] else 'не найдены'}\n"
    response += f"• Статистика: удалена из {removed['topics']} тем\n"
    response += f"• Пользователь: {'удалён' if removed['user'] else 'не найден'}"
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

async def cmd_adduser(update, context):
    admin_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("!adduser @username\n!adduser ID\n!adduser @username Ник", parse_mode=ParseMode.HTML)
        return
    
    if chat_id not in get_all_chats():
        add_chat_to_db(chat_id)
    
    target = context.args[0]
    custom = ' '.join(context.args[1:]) if len(context.args) > 1 else None
    target_user = None
    
    try:
        target_id = int(target)
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, target_id)
            if member and member.user:
                target_user = member.user
        except:
            target_user = User(id=target_id, first_name=custom or f"User {target_id}", is_bot=False)
    except ValueError:
        if target.startswith('@'):
            clean = target[1:]
            try:
                chat = await context.bot.get_chat(f"@{clean}")
                if chat and not chat.is_bot:
                    target_user = chat
            except:
                target_user = User(id=0, first_name=custom or clean, is_bot=False, username=clean)
    
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    if target_user.id == 0 and target_user.username:
        try:
            admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            for a in admins:
                if a.user.username and a.user.username.lower() == target_user.username.lower():
                    target_user = a.user
                    break
        except:
            pass
    
    if target_user.id == 0:
        await update.message.reply_text(f"❌ Не удалось получить ID. Используйте ID")
        return
    
    display = custom or target_user.full_name or f"User {target_user.id}"
    exists = user_exists_in_chat(target_user.id, chat_id)
    
    if not exists:
        get_or_create_user(target_user.id, chat_id, target_user.username or '', display)
        get_or_create_topic(chat_id, '0', 'Общая тема')
        add_user_to_topic(chat_id, '0', target_user.id, 0)
        
        if custom:
            set_user_custom_nick(target_user.id, custom)
        
        clickable = get_clickable_name(target_user.id, display, target_user.username or '')
        log_admin_action(admin_id, update.effective_user.full_name, "Ручное добавление", f"{target_user.id} (@{target_user.username})", f"Имя: {display}")
        
        response = f"✅ {clickable} добавлен!\n📝 Имя: {display}\n🆔 <code>{target_user.id}</code>"
        if target_user.username:
            response += f"\n👤 @{target_user.username}"
        if custom:
            response += f"\n🏷️ Ник: {custom}"
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
    else:
        if custom:
            set_user_custom_nick(target_user.id, custom)
            await update.message.reply_text(f"ℹ️ Пользователь уже есть. Ник обновлён на {custom}")
        else:
            await update.message.reply_text("ℹ️ Пользователь уже есть в базе")

def register(app):
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!ник\b'), cmd_nick))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!очистить\b'), cmd_clear_user))
    app.add_handler(CommandHandler("adduser", cmd_adduser))