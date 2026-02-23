"""
СИСТЕМА ОТПУСКОВ - ИСПРАВЛЕННАЯ ВЕРСИЯ
!отпуск, !мой отпуск, !сброс
"""
from datetime import datetime, timedelta
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
import traceback
from database import (
    set_vacation, get_vacation, end_vacation, reset_all_vacations,
    get_setting
)
from permissions import has_permission, is_admin, get_clickable_name
from user_resolver import resolve_user
from logger import log_user_action, log_admin_action

print("✅ vacation.py загружен!")

async def cmd_vacation(update, context):
    """!отпуск КОЛИЧЕСТВО_ДНЕЙ - уйти в отпуск"""
    print("\n🔥 ВЫПОЛНЕНИЕ !отпуск")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   user_id: {user_id}")
        
        if not has_permission(user_id, '!отпуск'):
            await update.message.reply_text("❌ Нет прав")
            return
        
        # Получаем количество дней из аргументов
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Укажите количество дней:\n"
                "<code>!отпуск 14</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        try:
            days = int(parts[1])
            print(f"   days: {days}")
            
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
            print("✅ Отпуск установлен")
            
            log_user_action(
                user_id=user_id,
                user_name=update.effective_user.full_name,
                action="Установка отпуска",
                details=f"на {days} дней"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Введите число дней")
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_vacation: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_my_vacation(update, context):
    """!мой отпуск - показать свой отпуск"""
    print("\n🔥 ВЫПОЛНЕНИЕ !мой отпуск")
    
    try:
        user_id = update.effective_user.id
        print(f"   user_id: {user_id}")
        
        target_id = user_id
        target_user = update.effective_user
        
        # Проверяем, есть ли аргументы (для просмотра чужого отпуска)
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) > 1:
            context.args = parts[1:]
            user = await resolve_user(update, context, required=True, allow_self=False)
            if user:
                target_id = user.id
                target_user = user
                print(f"   target: {target_id} - {target_user.first_name}")
        
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
        print("✅ Информация об отпуске отправлена")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_my_vacation: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_reset_vacations(update, context):
    """!сброс - сбросить все отпуска (только для админов)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !сброс")
    
    try:
        user_id = update.effective_user.id
        print(f"   admin_id: {user_id}")
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Только администраторы")
            return
        
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) < 2 or parts[1].lower() != 'confirm':
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
        print("✅ Все отпуска сброшены")
        
        log_admin_action(
            admin_id=user_id,
            admin_name=update.effective_user.full_name,
            action="Сброс всех отпусков"
        )
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_reset_vacations: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд vacation.py...")
    app.add_handler(MessageHandler(filters.Regex(r'^!отпуск\b'), cmd_vacation))
    app.add_handler(MessageHandler(filters.Regex(r'^!мой отпуск\b'), cmd_my_vacation))
    app.add_handler(MessageHandler(filters.Regex(r'^!сброс\b'), cmd_reset_vacations))
    print("✅ vacation.py зарегистрирован")