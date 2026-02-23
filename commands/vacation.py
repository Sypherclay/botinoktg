"""
СИСТЕМА ОТПУСКОВ
!отпуск, !мой отпуск, !сброс
"""
from datetime import datetime, timedelta
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
from database import (
    set_vacation, get_vacation, end_vacation, reset_all_vacations,
    get_setting
)
from permissions import has_permission, is_admin, get_clickable_name
from user_resolver import resolve_user
from logger import log_user_action, log_admin_action

async def cmd_vacation(update, context):
    """!отпуск КОЛИЧЕСТВО_ДНЕЙ - уйти в отпуск"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not has_permission(user_id, '!отпуск'):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите количество дней:\n"
            "<code>!отпуск 14</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        days = int(context.args[0])
        if days <= 0:
            await update.message.reply_text("❌ Количество дней должно быть положительным")
            return
        
        max_days = int(get_setting('max_vacation_days', '14'))
        if days > max_days:
            await update.message.reply_text(
                f"❌ Отпуск не может быть длиннее {max_days} дней.\n"
                f"Вы указали: {days} дней"
            )
            return
        
        existing = get_vacation(user_id)
        if existing:
            end_date = datetime.fromisoformat(existing[1]).strftime("%d.%m.%Y")
            await update.message.reply_text(f"❌ Вы уже в отпуске до {end_date}")
            return
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        set_vacation(
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        clickable = get_clickable_name(
            user_id,
            update.effective_user.first_name,
            update.effective_user.username
        )
        
        await update.message.reply_text(
            f"✅ {clickable}, вы ушли в отпуск на {days} дней!\n"
            f"📅 Начало: {start_date.strftime('%d.%m.%Y')}\n"
            f"📅 Окончание: {end_date.strftime('%d.%m.%Y')}",
            parse_mode=ParseMode.HTML
        )
        
        log_user_action(
            user_id=user_id,
            user_name=update.effective_user.full_name,
            action="Установка отпуска",
            details=f"на {days} дней"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Введите число дней")

async def cmd_my_vacation(update, context):
    """!мой отпуск - показать свой отпуск"""
    user_id = update.effective_user.id
    
    target_id = user_id
    target_user = update.effective_user
    
    if context.args:
        user = await resolve_user(update, context, required=True, allow_self=False)
        if user:
            target_id = user.id
            target_user = user
    
    vacation = get_vacation(target_id)
    clickable = get_clickable_name(target_id, target_user.first_name, target_user.username)
    
    if not vacation:
        await update.message.reply_text(
            f"ℹ️ {clickable} не в отпуске",
            parse_mode=ParseMode.HTML
        )
        return
    
    start_date, end_date, used_days = vacation
    start = datetime.fromisoformat(start_date).strftime("%d.%m.%Y")
    end = datetime.fromisoformat(end_date).strftime("%d.%m.%Y")
    
    remaining = max(0, (datetime.fromisoformat(end_date) - datetime.now()).days)
    total_days = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
    
    response = f"🏖 <b>Отпуск</b> — {clickable}\n\n"
    response += f"📅 Начало: {start}\n"
    response += f"📅 Окончание: {end}\n"
    response += f"⏱ Всего дней: {total_days}\n"
    response += f"📊 Использовано всего: {used_days}\n"
    response += f"⏳ Осталось: {remaining}"
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

async def cmd_reset_vacations(update, context):
    """!сброс - сбросить все отпуска (только для админов)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Только администраторы")
        return
    
    if not context.args or context.args[0].lower() != 'confirm':
        await update.message.reply_text(
            "⚠️ <b>Сброс всех отпусков</b>\n\n"
            "Для подтверждения введите:\n"
            "<code>!сброс confirm</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    reset_all_vacations()
    
    clickable = get_clickable_name(
        user_id,
        update.effective_user.first_name,
        update.effective_user.username
    )
    
    await update.message.reply_text(
        f"✅ {clickable} сбросил все отпуска!",
        parse_mode=ParseMode.HTML
    )
    
    log_admin_action(
        admin_id=user_id,
        admin_name=update.effective_user.full_name,
        action="Сброс всех отпусков"
    )

def register(app):
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!отпуск\b'), cmd_vacation))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!мой отпуск\b'), cmd_my_vacation))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!сброс\b'), cmd_reset_vacations))