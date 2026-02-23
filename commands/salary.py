"""
СИСТЕМА ЗАРПЛАТ - ИСПРАВЛЕННАЯ ВЕРСИЯ
!зп, !плюс, !минус, -зп
"""
from datetime import datetime, timedelta
from telegram.ext import MessageHandler, CommandHandler, filters
from telegram.constants import ParseMode
import sqlite3
import traceback
from database import (
    get_salary_counter, add_to_salary_counter, reset_salary_counter,
    get_user_balance, add_to_balance, subtract_from_balance,
    get_user_info, get_user_rank_db, get_setting,
    get_all_users_in_chat, get_payout_settings,
    save_payout_settings, DB_PATH
)
from permissions import is_admin, is_owner, get_user_rank, get_clickable_name
from user_resolver import resolve_user
from constants import RANKS, ANONYMOUS_ADMIN_ID, OWNER_ID
from logger import log_admin_action, log_command

print("✅ salary.py загружен!")

async def cmd_zp(update, context):
    """!зп - показать заработок пользователей"""
    print("\n🔥 ВЫПОЛНЕНИЕ !зп")
    
    try:
        chat_id = str(update.effective_chat.id)
        print(f"   chat_id: {chat_id}")
        
        users = []
        for uid, name, username in get_all_users_in_chat(chat_id):
            counter = get_salary_counter(uid)
            balance = get_user_balance(uid)
            if counter > 0 or balance > 0:
                clickable = get_clickable_name(uid, name, username)
                users.append({'name': clickable, 'counter': counter, 'balance': balance})
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей с данными о зарплатах")
            return
        
        users.sort(key=lambda x: x['balance'], reverse=True)
        
        lines = ["💰 <b>Заработок пользователей</b>", ""]
        for u in users:
            lines.append(f"👤 {u['name']}")
            lines.append(f"   💰 Накоплено к выплате: {u['counter']}")
            lines.append(f"   💵 Баланс: {u['balance']} HC")
            lines.append("")
        
        lines.append(f"👥 Всего: {len(users)} пользователей")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        print("✅ !зп выполнена")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_zp: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_plus(update, context):
    """!плюс число - начислить коины (ответом на сообщение)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !плюс")
    
    try:
        user_id = update.effective_user.id
        print(f"   admin_id: {user_id}")
        
        if not (is_admin(user_id) or is_owner(user_id)):
            await update.message.reply_text("❌ Только администраторы")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Ответьте на сообщение пользователя")
            return
        
        # Получаем число из аргументов
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) < 2:
            await update.message.reply_text("!плюс число (ответом)")
            return
        
        try:
            amount = int(parts[1])
            if amount <= 0:
                await update.message.reply_text("❌ Число должно быть положительным")
                return
        except ValueError:
            await update.message.reply_text("❌ Укажите число")
            return
        
        target = update.message.reply_to_message.from_user
        print(f"   target: {target.id} - {target.first_name}")
        
        new = add_to_balance(target.id, amount)
        clickable = get_clickable_name(target.id, target.first_name, target.username)
        
        await update.message.reply_text(
            f"✅ Начислено {amount} HC {clickable}\n💰 Баланс: {new}",
            parse_mode=ParseMode.HTML
        )
        print(f"✅ Начислено {amount} HC")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_plus: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_minus(update, context):
    """!минус число - списать коины (ответом на сообщение)"""
    print("\n🔥 ВЫПОЛНЕНИЕ !минус")
    
    try:
        user_id = update.effective_user.id
        print(f"   admin_id: {user_id}")
        
        if not (is_admin(user_id) or is_owner(user_id)):
            await update.message.reply_text("❌ Только администраторы")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Ответьте на сообщение пользователя")
            return
        
        # Получаем число из аргументов
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) < 2:
            await update.message.reply_text("!минус число (ответом)")
            return
        
        try:
            amount = int(parts[1])
            if amount <= 0:
                await update.message.reply_text("❌ Число должно быть положительным")
                return
        except ValueError:
            await update.message.reply_text("❌ Укажите число")
            return
        
        target = update.message.reply_to_message.from_user
        print(f"   target: {target.id} - {target.first_name}")
        
        success, new = subtract_from_balance(target.id, amount)
        clickable = get_clickable_name(target.id, target.first_name, target.username)
        
        if success:
            await update.message.reply_text(
                f"✅ Списано {amount} HC у {clickable}\n💰 Баланс: {new}",
                parse_mode=ParseMode.HTML
            )
            print(f"✅ Списано {amount} HC")
        else:
            await update.message.reply_text(
                f"❌ У {clickable} недостаточно средств\n💰 Баланс: {new}",
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        print(f"❌ Ошибка в cmd_minus: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_plus_reply(update, context):
    """Команда '+' - +1 к счётчику (только ответом)"""
    print("\n🔥 ВЫПОЛНЕНИЕ +")
    
    try:
        user_id = update.effective_user.id
        print(f"   admin_id: {user_id}")
        
        if not (is_admin(user_id) or get_user_rank(user_id) == 'curator'):
            await update.message.reply_text("❌ Только админы и кураторы")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Только ответом на сообщение")
            return
        
        target = update.message.reply_to_message.from_user
        print(f"   target: {target.id} - {target.first_name}")
        
        if target.id == user_id:
            await update.message.reply_text("❌ Нельзя начислять себе")
            return
        
        if target.is_bot:
            await update.message.reply_text("❌ Нельзя начислять боту")
            return
        
        new = add_to_salary_counter(target.id, 1)
        balance = get_user_balance(target.id)
        clickable = get_clickable_name(target.id, target.first_name, target.username)
        
        await update.message.reply_text(
            f"✅ Счётчик для {clickable} +1\n📊 Текущий: {new}\n💰 Баланс: {balance} HC",
            parse_mode=ParseMode.HTML
        )
        print(f"✅ Счётчик увеличен: {new}")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_plus_reply: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_remove_from_salary(update, context):
    """-зп - удалить пользователя из системы зарплат"""
    print("\n🔥 ВЫПОЛНЕНИЕ -зп")
    
    try:
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        
        print(f"   admin_id: {user_id}")
        
        if not (is_admin(user_id) or get_user_rank(user_id) == 'curator'):
            await update.message.reply_text("❌ Только админы и кураторы")
            return
        
        # Получаем цель из аргументов
        message_text = update.message.text
        parts = message_text.split()
        
        if len(parts) < 2 and not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ Укажите пользователя:\n"
                "-зп @username\n"
                "-зп ID\n"
                "Или ответьте на сообщение",
                parse_mode=ParseMode.HTML
            )
            return
        
        if len(parts) > 1:
            context.args = parts[1:]
        
        user = await resolve_user(update, context)
        if not user:
            return
        
        print(f"   target: {user.id} - {user.first_name}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT salary_counter, balance FROM salary WHERE user_id = ?', (user.id,))
        data = cursor.fetchone()
        counter = data[0] if data else 0
        balance = data[1] if data else 0
        cursor.execute('DELETE FROM salary WHERE user_id = ?', (user.id,))
        conn.commit()
        conn.close()
        
        clickable = get_clickable_name(user.id, user.first_name, user.username)
        
        await update.message.reply_text(
            f"✅ {clickable} удалён из системы зарплат!\n\n"
            f"📊 Было:\n"
            f"   • Счётчик: {counter}\n"
            f"   • Баланс: {balance} HC",
            parse_mode=ParseMode.HTML
        )
        print(f"✅ Пользователь удалён из зарплат")
        
    except Exception as e:
        print(f"❌ Ошибка в cmd_remove_from_salary: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд salary.py...")
    # Английские команды через CommandHandler
    app.add_handler(CommandHandler("addzarplata", lambda u,c: None))  # Заглушка, реализуй если нужно
    app.add_handler(CommandHandler("removezarplata", lambda u,c: None))  # Заглушка
    app.add_handler(CommandHandler("zptest", lambda u,c: None))  # Заглушка
    
    # Русские команды через MessageHandler
    app.add_handler(MessageHandler(filters.Regex(r'^!зп\b'), cmd_zp))
    app.add_handler(MessageHandler(filters.Regex(r'^!плюс\b'), cmd_plus))
    app.add_handler(MessageHandler(filters.Regex(r'^!минус\b'), cmd_minus))
    app.add_handler(MessageHandler(filters.Regex(r'^-зп\b'), cmd_remove_from_salary))
    app.add_handler(MessageHandler(filters.Regex(r'^\+$'), cmd_plus_reply))
    print("✅ salary.py зарегистрирован")