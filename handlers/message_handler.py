"""
ГЛАВНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ
Статистика, авто-варны, юбилеи
"""
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import (
    get_or_create_user, update_user_stats, get_or_create_topic,
    update_topic_stats, get_user_topic_count, is_first_in_album,
    cleanup_old_groups, is_auto_warn_enabled, is_whitelisted,
    update_user_activity, get_milestone_tracked_topics,
    get_user_achieved_milestones, add_user_milestone,
    get_user_custom_nick, get_milestone_message, get_user_info
)
from logger import log_auto_warn
from commands.autowarn import process_auto_warn

# ========== ФУНКЦИЯ ПРЯМО ЗДЕСЬ ==========
def check_milestones(user_id, chat_id, topic_id, message_count):
    """Проверка достижения юбилейных отметок"""
    try:
        tracked_topics = get_milestone_tracked_topics()
        if str(topic_id) not in tracked_topics:
            return None
        
        achieved = get_user_achieved_milestones(user_id, chat_id)
        milestones = [500, 1000, 1500, 2000, 2500, 3000]
        
        for milestone in milestones:
            if message_count >= milestone and milestone not in achieved:
                add_user_milestone(user_id, chat_id, milestone)
                
                custom_nick = get_user_custom_nick(user_id)
                if custom_nick:
                    user_display_name = custom_nick
                else:
                    user_info = get_user_info(user_id, chat_id)
                    if user_info:
                        user_display_name = user_info[0]
                    else:
                        user_display_name = f"Пользователь {user_id}"
                
                message_template = get_milestone_message(milestone)
                if message_template:
                    congrat_message = message_template.format(ник=user_display_name)
                    return congrat_message
    except Exception as e:
        print(f"Ошибка в check_milestones: {e}")
    
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех входящих сообщений"""
    
    if not update.message:
        return
    
    print(f"\n🔥 ПОЛУЧЕНО СООБЩЕНИЕ: {update.message.text}")
    
    # ========== НОВЫЕ УЧАСТНИКИ ==========
    if update.message.new_chat_members:
        from commands.welcome import handle_new_member
        await handle_new_member(update, context)
        return
    
    # ========== ВЫХОД УЧАСТНИКА ==========
    if update.message.left_chat_member:
        left = update.message.left_chat_member
        if not left.is_bot:
            print(f"Пользователь {left.id} покинул чат")
        return
    
    # ========== ОСНОВНАЯ СТАТИСТИКА ==========
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    
    # Тема
    topic_id = "0"
    topic_name = "Общий"
    if hasattr(update.message, 'message_thread_id') and update.message.message_thread_id:
        topic_id = str(update.message.message_thread_id)
        if hasattr(update.message, 'forum_topic_created') and update.message.forum_topic_created:
            topic_name = update.message.forum_topic_created.name
    
    # Тип сообщения
    has_photo = bool(update.message.photo)
    has_video = bool(update.message.video)
    has_document = bool(update.message.document)
    has_audio = bool(update.message.audio)
    has_voice = bool(update.message.voice)
    has_sticker = bool(update.message.sticker)
    has_animation = bool(update.message.animation)
    
    has_media = has_photo or has_video or has_document or has_audio or has_voice or has_sticker or has_animation
    has_text = bool(update.message.text or update.message.caption)
    
    print(f"📊 has_media={has_media}, has_text={has_text}")
    
    # Альбомы
    is_first = True
    if update.message.media_group_id:
        is_first = is_first_in_album(update.message.media_group_id)
        print(f"🖼️ Альбом: {'первое' if is_first else 'не первое'}")
    
    # Периодическая очистка
    if random.randint(1, 100) == 1:
        cleanup_old_groups()
    
    # Проверка авто-варн темы
    is_auto_topic = is_auto_warn_enabled(topic_id)
    print(f"   Тема в списке авто-варнов: {is_auto_topic}")
    
    # ========== АВТО-ВАРНЫ ==========
    if is_first and is_auto_topic and not is_whitelisted(user_id):
        if has_text and not has_media:
            print("⚠️ Только текст - даём варн")
            await process_auto_warn(update, context, user_id, True, True)
        elif not has_text and has_media:
            print("⚠️ Только медиа - даём варн")
            await process_auto_warn(update, context, user_id, True, False)
        elif has_text and has_media:
            print("✅ Текст+медиа - ОК")
    
    # ========== СОХРАНЕНИЕ В БД ==========
    if is_first:
        # Пользователь
        username = update.effective_user.username or ''
        name = update.effective_user.full_name or f"User {user_id}"
        get_or_create_user(user_id, chat_id, username, name)
        
        # Тема
        get_or_create_topic(chat_id, topic_id, topic_name)
        
        # Статистика
        update_user_stats(
            user_id, chat_id,
            has_media, has_text,
            bool(update.message.media_group_id),
            is_auto_topic
        )
        
        # Статистика темы
        update_topic_stats(chat_id, topic_id, user_id)
        
        # ========== ЮБИЛЕИ ==========
        count = get_user_topic_count(chat_id, topic_id, user_id)
        msg = check_milestones(user_id, chat_id, topic_id, count)
        
        if msg:
            print(f"🏆 Юбилей: {msg}")
            await update.message.reply_text(
                msg,
                reply_to_message_id=update.message.message_id
            )
        
        # ========== АКТИВНОСТЬ ==========
        update_user_activity(user_id, chat_id)
    
    print("💾 Данные сохранены в БД\n")