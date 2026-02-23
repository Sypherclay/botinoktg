"""
НАПОМИНАНИЯ О НЕАКТИВНОСТИ
/notifyactive
"""
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
from database import get_reminder_settings, save_reminder_settings
from permissions import is_admin

async def cmd_notifyactive(update, context):
    """Управление напоминаниями о неактивности"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    settings = get_reminder_settings()
    
    if not context.args:
        status = "✅ Вкл" if settings.get('enabled', True) else "❌ Выкл"
        intervals = settings.get('intervals', {})
        
        text = (
            f"🔔 <b>Напоминания о неактивности</b>\n\n"
            f"<b>Статус:</b> {status}\n\n"
            f"<b>Интервалы:</b>\n"
            f"• 1 день: {'✅' if intervals.get('1_day', True) else '❌'}\n"
            f"• 3 дня: {'✅' if intervals.get('3_days', True) else '❌'}\n"
            f"• 7 дней: {'✅' if intervals.get('7_days', True) else '❌'}\n"
            f"• 14 дней: {'✅' if intervals.get('14_days', True) else '❌'}\n\n"
            f"<b>Команды:</b>\n"
            f"• /notifyactive on - включить\n"
            f"• /notifyactive off - выключить\n"
            f"• /notifyactive reset - сбросить историю\n"
            f"• /notifyactive 1day on/off - управление интервалами\n"
            f"• /notifyactive 3days on/off\n"
            f"• /notifyactive 7days on/off\n"
            f"• /notifyactive 14days on/off"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
    
    cmd = context.args[0].lower()
    
    if cmd == "on":
        settings['enabled'] = True
        save_reminder_settings(settings)
        await update.message.reply_text("✅ Напоминания включены")
    
    elif cmd == "off":
        settings['enabled'] = False
        save_reminder_settings(settings)
        await update.message.reply_text("✅ Напоминания выключены")
    
    elif cmd == "reset":
        settings['sent_reminders'] = {}
        save_reminder_settings(settings)
        await update.message.reply_text("✅ История сброшена")
    
    elif cmd == "1day" and len(context.args) > 1:
        val = context.args[1].lower()
        settings['intervals']['1_day'] = val in ['on', 'true', '1']
        save_reminder_settings(settings)
        await update.message.reply_text(f"✅ 1 день {'включён' if settings['intervals']['1_day'] else 'выключен'}")
    
    elif cmd == "3days" and len(context.args) > 1:
        val = context.args[1].lower()
        settings['intervals']['3_days'] = val in ['on', 'true', '1']
        save_reminder_settings(settings)
        await update.message.reply_text(f"✅ 3 дня {'включены' if settings['intervals']['3_days'] else 'выключены'}")
    
    elif cmd == "7days" and len(context.args) > 1:
        val = context.args[1].lower()
        settings['intervals']['7_days'] = val in ['on', 'true', '1']
        save_reminder_settings(settings)
        await update.message.reply_text(f"✅ 7 дней {'включены' if settings['intervals']['7_days'] else 'выключены'}")
    
    elif cmd == "14days" and len(context.args) > 1:
        val = context.args[1].lower()
        settings['intervals']['14_days'] = val in ['on', 'true', '1']
        save_reminder_settings(settings)
        await update.message.reply_text(f"✅ 14 дней {'включены' if settings['intervals']['14_days'] else 'выключены'}")
    
    else:
        await update.message.reply_text("❌ Неизвестная команда. /notifyactive для справки")

def register(app):
    app.add_handler(CommandHandler("notifyactive", cmd_notifyactive))