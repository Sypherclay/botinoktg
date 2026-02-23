"""
АДМИНИСТРИРОВАНИЕ БОТА
Команды: /addadmin, /removeadmin, /listadmins
"""
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
from permissions import is_owner
from database import get_all_admins, add_admin_db, remove_admin_db, get_user_info
from user_resolver import resolve_user
from logger import log_admin_action, log_command

async def cmd_addadmin(update, context):
    """Добавить администратора /addadmin"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ Только владелец может добавлять администраторов")
        return
    
    if not context.args:
        await update.message.reply_text("Используйте: /addadmin ID_пользователя")
        return
    
    try:
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
        
        log_command(
            "/addadmin",
            user_id,
            admin_name,
            chat_id,
            f"Добавлен администратор: {new_admin_id}"
        )
        
        await update.message.reply_text(f"✅ Пользователь {new_admin_id} добавлен как администратор")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. ID должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def cmd_removeadmin(update, context):
    """Удалить администратора /removeadmin"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ Только владелец может удалять администраторов")
        return
    
    if not context.args:
        await update.message.reply_text("Используйте: /removeadmin ID_пользователя")
        return
    
    try:
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
        
        log_command(
            "/removeadmin",
            user_id,
            admin_name,
            chat_id,
            f"Удален администратор: {admin_id_to_remove}"
        )
        
        await update.message.reply_text(f"✅ Пользователь {admin_id_to_remove} удален из администраторов")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. ID должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def cmd_listadmins(update, context):
    """Показать список администраторов /listadmins"""
    user_id = update.effective_user.id
    
    from permissions import is_admin
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
        # Пробуем получить имя
        user_info = get_user_info(admin_id, str(update.effective_chat.id))
        if user_info:
            name, _ = user_info
            text += f"{i}. <code>{admin_id}</code> - {name} - {status}\n"
        else:
            text += f"{i}. <code>{admin_id}</code> - {status}\n"
    
    text += f"\n<b>📊 Всего:</b> {len(admins)} администратор(ов)"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

def register(app):
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    app.add_handler(CommandHandler("removeadmin", cmd_removeadmin))
    app.add_handler(CommandHandler("listadmins", cmd_listadmins))