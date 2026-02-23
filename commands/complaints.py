"""
СИСТЕМА ЖАЛОБ
!жалоба
"""
import re
from telegram.ext import MessageHandler, filters
from telegram.constants import ParseMode
from database import (
    get_all_admins, get_all_users_with_rank,
    increment_complaint_count, has_reward, add_reward
)
from permissions import get_clickable_name

async def cmd_complaint(update, context):
    """!жалоба [текст] - пожаловаться на сообщение (ответом)"""
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение с наказанием")
        return
    
    replied = update.message.reply_to_message
    complainant = update.effective_user
    
    text = ' '.join(context.args) if context.args else "Без объяснения"
    
    admins = get_all_admins()
    curators = get_all_users_with_rank('curator')
    notify = set(admins + curators)
    
    chat_id = str(update.effective_chat.id)
    if chat_id.startswith('-100'):
        chat_short = chat_id[4:]
    else:
        chat_short = chat_id
    
    punish_link = f"https://t.me/c/{chat_short}/{replied.message_id}"
    complaint_link = f"https://t.me/c/{chat_short}/{update.message.message_id}"
    
    complainant_name = get_clickable_name(
        complainant.id,
        complainant.first_name,
        complainant.username
    )
    
    helper_id = None
    msg_text = replied.text or replied.caption or ""
    
    id_match = re.search(r'tg://user\?id=(\d+)', msg_text)
    if id_match:
        helper_id = int(id_match.group(1))
    
    if not helper_id:
        nums = re.findall(r'\b(\d+)\b', msg_text)
        for n in nums:
            pid = int(n)
            if pid > 1000000:
                helper_id = pid
                break
    
    helper_text = f"🆔 <b>ID хелпера:</b> <code>{helper_id}</code>\n" if helper_id else ""
    
    sent = 0
    for aid in notify:
        try:
            await context.bot.send_message(
                chat_id=aid,
                text=(
                    f"📨 <b>ЖАЛОБА</b>\n\n"
                    f"👤 <b>Ябеда:</b> {complainant_name}\n"
                    f"📝 <b>Причина:</b> {text}\n"
                    f"🔗 <b>Наказание:</b> <a href='{punish_link}'>перейти</a>\n"
                    f"💬 <b>Жалоба:</b> <a href='{complaint_link}'>перейти</a>\n"
                    f"{helper_text}"
                    f"\n⚡️ <b>Действия:</b>\n"
                    f"💰 <code>+</code> (ответом) — если жалоба верна\n"
                    f"⚠️ <code>!выговор</code> (ответом) — если ложная"
                ),
                parse_mode=ParseMode.HTML
            )
            sent += 1
        except:
            pass
    
    new_count = increment_complaint_count(complainant.id)
    
    if new_count >= 10 and not has_reward(complainant.id, '10_complaints'):
        add_reward(complainant.id, '10_complaints')
        try:
            await context.bot.send_message(
                chat_id=complainant.id,
                text="🎉 <b>Поздравляем!</b>\n\nВы подали 10 жалоб и получили награду: 💸 ЗА ДЕНЬГИ ДА",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
    
    progress = f"\n📊 Прогресс: {new_count}/10 жалоб" if new_count < 10 else f"\n🏆 Всего жалоб: {new_count}"
    
    await update.message.reply_text(
        f"✅ Жалоба отправлена {sent} кураторам!{progress}",
        parse_mode=ParseMode.HTML
    )

def register(app):
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'^!жалоба\b'), cmd_complaint))