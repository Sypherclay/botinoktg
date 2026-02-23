"""
АДМИНИСТРИРОВАНИЕ БОТА - ИСПРАВЛЕННАЯ ВЕРСИЯ
Команды: /addadmin, /removeadmin, /listadmins, /setkicktopic, /resetkicktopic
"""
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
import traceback
from permissions import is_owner, is_admin, get_clickable_name  # ← ДОБАВЛЕН ИМПОРТ!
from database import get_all_admins, add_admin_db, remove_admin_db, get_user_info, get_kick_topic_id, set_kick_topic_id
from user_resolver import resolve_user
from logger import log_admin_action, log_command

print("✅ admin.py загружен!")

async def cmd_addadmin(update, context):
    """Добавить администратора /addadmin"""
    print("\n🔥 ВЫПОЛНЕНИЕ /addadmin")
    
    try:
        user_id = update.effective_user.id
        
        if not is_owner(user_id):
            await update.message.reply_text("❌ Только владелец может добавлять администраторов")
            return
        
        if not context.args:
            await update.message.reply_text("Используйте: /addadmin ID_пользователя")
            return
        
        new_admin_id = int(context.args[0])
        admins = get_all_admins()
        
        if new_admin_id in admins:
            await update.message.reply_text(f"ℹ️ Пользователь {new_admin_id} уже является администратором")
            return
        
        add_admin_db(new_admin_id)
        
        admin_name = update.effective_user.full_name or str(user_id)
        
        log_admin_action(
            admin_id=user_id,
            admin_name=admin_name,
            action="Добавил администратора",
            target=str(new_admin_id)
        )
        
        await update.message.reply_text(f"✅ Пользователь {new_admin_id} добавлен как администратор")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_removeadmin(update, context):
    """Удалить администратора /removeadmin"""
    print("\n🔥 ВЫПОЛНЕНИЕ /removeadmin")
    
    try:
        user_id = update.effective_user.id
        
        if not is_owner(user_id):
            await update.message.reply_text("❌ Только владелец может удалять администраторов")
            return
        
        if not context.args:
            await update.message.reply_text("Используйте: /removeadmin ID_пользователя")
            return
        
        admin_id_to_remove = int(context.args[0])
        admins = get_all_admins()
        
        from config import OWNER_ID
        if admin_id_to_remove == OWNER_ID:
            await update.message.reply_text("❌ Нельзя удалить владельца из списка администраторов")
            return
        
        if admin_id_to_remove not in admins:
            await update.message.reply_text(f"❌ Пользователь {admin_id_to_remove} не является администратором")
            return
        
        remove_admin_db(admin_id_to_remove)
        
        admin_name = update.effective_user.full_name or str(user_id)
        
        log_admin_action(
            admin_id=user_id,
            admin_name=admin_name,
            action="Удалил администратора",
            target=str(admin_id_to_remove)
        )
        
        await update.message.reply_text(f"✅ Пользователь {admin_id_to_remove} удален из администраторов")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_listadmins(update, context):
    """Показать список администраторов /listadmins"""
    print("\n🔥 ВЫПОЛНЕНИЕ /listadmins")
    
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        admins = get_all_admins()
        from config import OWNER_ID
        
        if not admins:
            await update.message.reply_text("📭 Нет администраторов")
            return
        
        text = "<b>👥 Список администраторов:</b>\n\n"
        
        for i, admin_id in enumerate(admins, 1):
            status = "👑 Владелец" if admin_id == OWNER_ID else "🛡️ Администратор"
            user_info = get_user_info(admin_id, str(update.effective_chat.id))
            if user_info and user_info[0]:
                name, _ = user_info
                text += f"{i}. <code>{admin_id}</code> - {name} - {status}\n"
            else:
                text += f"{i}. <code>{admin_id}</code> - {status}\n"
        
        text += f"\n<b>📊 Всего:</b> {len(admins)} администратор(ов)"
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

# ========== НОВЫЕ КОМАНДЫ ==========

async def cmd_setkicktopic(update, context):
    """Установить тему для сообщений о киках /setkicktopic ID"""
    print("\n🔥 ВЫПОЛНЕНИЕ /setkicktopic")
    
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        if not context.args:
            current_topic = get_kick_topic_id()
            if current_topic:
                await update.message.reply_text(
                    f"ℹ️ Текущая тема для киков: <code>{current_topic}</code>\n"
                    f"Используйте: /setkicktopic ID_темы",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    "ℹ️ Тема для киков не установлена.\n"
                    "Используйте: /setkicktopic ID_темы",
                    parse_mode=ParseMode.HTML
                )
            return
        
        topic_id = context.args[0]
        
        try:
            int(topic_id)
            set_kick_topic_id(topic_id)
            
            admin_name = update.effective_user.full_name
            
            # УБИРАЕМ get_clickable_name если он не нужен
            await update.message.reply_text(
                f"✅ Тема для сообщений о киках установлена: <code>{topic_id}</code>",
                parse_mode=ParseMode.HTML
            )
            
            log_admin_action(
                admin_id=update.effective_user.id,
                admin_name=admin_name,
                action="Установил тему для киков",
                details=f"Тема ID: {topic_id}"
            )
        except ValueError:
            await update.message.reply_text("❌ ID темы должен быть числом")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

async def cmd_resetkicktopic(update, context):
    """Сбросить тему для сообщений о киках /resetkicktopic"""
    print("\n🔥 ВЫПОЛНЕНИЕ /resetkicktopic")
    
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        current_topic = get_kick_topic_id()
        set_kick_topic_id(None)
        
        admin_name = update.effective_user.full_name
        
        if current_topic:
            await update.message.reply_text(
                f"✅ Тема для киков сброшена: <code>{current_topic}</code>",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                "ℹ️ Тема для киков и так не была установлена.",
                parse_mode=ParseMode.HTML
            )
        
        log_admin_action(
            admin_id=update.effective_user.id,
            admin_name=admin_name,
            action="Сбросил тему для киков",
            details=f"Была установлена тема: {current_topic if current_topic else 'не установлена'}"
        )
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

def register(app):
    print("📝 Регистрация команд admin.py...")
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    app.add_handler(CommandHandler("removeadmin", cmd_removeadmin))
    app.add_handler(CommandHandler("listadmins", cmd_listadmins))
    app.add_handler(CommandHandler("setkicktopic", cmd_setkicktopic))
    app.add_handler(CommandHandler("resetkicktopic", cmd_resetkicktopic))
    print("✅ admin.py зарегистрирован")