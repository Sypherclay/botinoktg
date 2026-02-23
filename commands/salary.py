"""
СИСТЕМА ЗАРПЛАТ - ИСПРАВЛЕННАЯ ВЕРСИЯ
!зп, !плюс, !минус, -зп, /addzarplata, /removezarplata, /zptest
"""
from datetime import datetime, timedelta
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
import sqlite3
import traceback
from database import (
    get_salary_counter, add_to_salary_counter, reset_salary_counter,
    get_user_balance, add_to_balance, subtract_from_balance,
    get_user_info, get_user_rank_db, get_setting, set_setting,
    get_all_users_in_chat, add_payout_history, get_payout_settings,
    save_payout_settings, DB_PATH
)
from permissions import is_admin, is_owner, get_user_rank, get_clickable_name
from user_resolver import resolve_user
from constants import RANKS, ANONYMOUS_ADMIN_ID, OWNER_ID
from logger import log_admin_action, log_command

print("✅ salary.py загружен!")

# ========== КОМАНДЫ УПРАВЛЕНИЯ ТЕМОЙ ==========

async def cmd_addzarplata(update, context):
    """Установить тему для выплат /addzarplata ID_темы"""
    print("\n🔥 ВЫПОЛНЕНИЕ /addzarplata")
    
    try:
        user_id = update.effective_user.id
        
        if not (is_admin(user_id) or is_owner(user_id)):
            await update.message.reply_text("❌ Только администраторы могут использовать эту команду")
            return
        
        settings = get_payout_settings()
        
        if not context.args:
            current = settings.get('payout_topic_id')
            if current:
                await update.message.reply_text(
                    f"ℹ️ Текущая тема для зарплат: <code>{current}</code>\n"
                    f"Используйте: /addzarplata ID_темы",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    "Используйте: /addzarplata ID_темы\n"
                    "Пример: /addzarplata 123",
                    parse_mode=ParseMode.HTML
                )
            return
        
        topic_id = context.args[0]
        
        try:
            int(topic_id)
            
            now = datetime.now()
            settings['payout_topic_id'] = topic_id
            settings['topic_set_date'] = now.isoformat()
            settings['last_payout'] = None
            settings['next_payout'] = (now + timedelta(days=30)).isoformat()
            
            save_payout_settings(settings)
            
            first_payout_date = (now + timedelta(days=30)).strftime("%d.%m.%Y")
            
            clickable_admin = get_clickable_name(
                user_id,
                update.effective_user.first_name,
                update.effective_user.username
            )
            
            await update.message.reply_text(
                f"✅ {clickable_admin} установил тему для выплат: <code>{topic_id}</code>\n"
                f"📅 Отсчет 30 дней начат!\n"
                f"💰 Первая выплата: {first_payout_date}",
                parse_mode=ParseMode.HTML
            )
            
            log_admin_action(
                admin_id=user_id,
                admin_name=update.effective_user.full_name,
                action="Установил тему для зарплат",
                details=f"Тема ID: {topic_id}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ ID темы должен быть числом")
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_addzarplata: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_removezarplata(update, context):
    """Удалить тему для выплат /removezarplata"""
    print("\n🔥 ВЫПОЛНЕНИЕ /removezarplata")
    
    try:
        user_id = update.effective_user.id
        
        if not (is_admin(user_id) or is_owner(user_id)):
            await update.message.reply_text("❌ Только администраторы могут использовать эту команду")
            return
        
        settings = get_payout_settings()
        current_topic = settings.get('payout_topic_id')
        
        settings['payout_topic_id'] = None
        settings['topic_set_date'] = None
        settings['last_payout'] = None
        settings['next_payout'] = None
        
        save_payout_settings(settings)
        
        clickable_admin = get_clickable_name(
            user_id,
            update.effective_user.first_name,
            update.effective_user.username
        )
        
        if current_topic:
            await update.message.reply_text(
                f"✅ {clickable_admin} удалил тему для зарплат: <code>{current_topic}</code>\n"
                f"🔄 Настройки зарплат сброшены!",
                parse_mode=ParseMode.HTML
            )
            
            log_admin_action(
                admin_id=user_id,
                admin_name=update.effective_user.full_name,
                action="Удалил тему для зарплат",
                details=f"Была тема: {current_topic}"
            )
        else:
            await update.message.reply_text(
                "ℹ️ Тема для зарплат и так не была установлена",
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_removezarplata: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_zptest(update, context):
    """Тестовый расчёт зарплат"""
    print("\n🔥 ВЫПОЛНЕНИЕ /zptest")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Только администраторы")
            return
        
        settings = get_payout_settings()
        topic = settings.get('payout_topic_id')
        
        if not topic:
            await update.message.reply_text(
                "❌ Тема для выплат не настроена.\n"
                "Используйте /addzarplata ID_темы",
                parse_mode=ParseMode.HTML
            )
            return
        
        rate = int(settings.get('rate_per_punishment', 10))
        
        users = []
        total = 0
        
        for uid, name, username in get_all_users_in_chat(chat_id):
            count = get_salary_counter(uid)
            if count > 0:
                salary = count * rate
                rank = get_user_rank_db(uid)
                rank_name = RANKS.get(rank, {}).get('name', 'Участник')
                clickable = get_clickable_name(uid, name, username)
                users.append({
                    'rank': rank,
                    'rank_name': rank_name,
                    'name': clickable,
                    'count': count,
                    'salary': salary
                })
                total += salary
        
        users.sort(key=lambda x: x['salary'], reverse=True)
        
        lines = ["🧪 <b>ТЕСТОВЫЙ РАСЧЁТ ЗАРПЛАТ</b>", "="*35]
        
        topic_set = settings.get('topic_set_date')
        if topic_set:
            d = datetime.fromisoformat(topic_set)
            lines.append(f"📅 Тема установлена: {d.strftime('%d.%m.%Y')}")
        
        lines.append(f"💎 Курс: {rate} HC за наказание")
        lines.append("="*35 + "\n")
        
        for u in users:
            lines.append(f"🎖️ <b>{u['rank_name']}</b> {u['name']}")
            lines.append(f"   📊 Накоплено наказаний: {u['count']}")
            lines.append(f"   💰 Получит: {u['salary']} HC\n")
        
        lines.append("="*35)
        lines.append(f"📊 Всего к выплате: {total} HC")
        lines.append(f"👥 Получат зарплату: {len(users)} человек")
        lines.append("="*35)
        lines.append("\n🔄 <i>Это тестовый расчет. Счетчики не сбрасываются</i>")
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=int(topic),
            text="\n".join(lines),
            parse_mode=ParseMode.HTML
        )
        
        await update.message.reply_text("✅ Тестовый расчет отправлен в тему для зарплат")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_zptest: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

# ... остальные команды (!зп, !плюс, !минус и т.д.) ...

def register(app):
    print("📝 Регистрация команд salary.py...")
    app.add_handler(CommandHandler("addzarplata", cmd_addzarplata))
    app.add_handler(CommandHandler("removezarplata", cmd_removezarplata))
    app.add_handler(CommandHandler("zptest", cmd_zptest))
    
    # Русские команды через MessageHandler
    app.add_handler(MessageHandler(filters.Regex(r'^!зп\b'), cmd_zp))
    app.add_handler(MessageHandler(filters.Regex(r'^!плюс\b'), cmd_plus))
    app.add_handler(MessageHandler(filters.Regex(r'^!минус\b'), cmd_minus))
    app.add_handler(MessageHandler(filters.Regex(r'^-зп\b'), cmd_remove_from_salary))
    app.add_handler(MessageHandler(filters.Regex(r'^\+$'), cmd_plus_reply))
    print("✅ salary.py зарегистрирован")