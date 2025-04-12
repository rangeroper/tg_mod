import os
from dotenv import load_dotenv
from telegram import Update, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from datetime import timedelta
import re
import json

load_dotenv()  # Load .env vars

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# File path for filters
FILTERS_FILE = "filters.json"

# File path for accompanying filter media
MEDIA_FOLDER = "media"

# File paths for phrases
BAN_PHRASES_FILE = "ban_phrases.txt"
MUTE_PHRASES_FILE = "mute_phrases.txt"
DELETE_PHRASES = "delete_phrases.txt"

# Mute duration in seconds (3 days)
MUTE_DURATION = 3 * 24 * 60 * 60

def load_phrases(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip().lower() for line in file.readlines()]
    
# Load filters as dict
def load_filters(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

FILTERS = load_filters(FILTERS_FILE)

# Load phrases from files
BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES)

def check_message(update: Update, context: CallbackContext):
    print(f"[DEBUG] Chat ID: {update.effective_chat.id}")

def check_message(update: Update, context: CallbackContext):
    message = update.message or update.channel_post  # Handle both messages and channel posts
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = update.effective_user

    # Fetch chat admins to prevent acting on their messages
    chat_admins = context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in chat_admins]

    if not message or not message.text:
        return  # Skip non-text or unsupported messages

    message_text = message.text.lower()
    print(f"[DEBUG] Received message: '{message_text}' from user: {user.first_name} (ID: {user_id})")

    if user_id not in admin_ids:
        # Check for ban phrases
        for phrase in BAN_PHRASES:
            if phrase in message_text:
                print(f"[BAN MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                message.reply_text(f"arc angel fallen. {user.first_name} has been banned.")
                return

        # Check for mute phrases
        for phrase in MUTE_PHRASES:
            if phrase in message_text:
                print(f"[MUTE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                until_date = message.date + timedelta(seconds=MUTE_DURATION)
                permissions = ChatPermissions(can_send_messages=False)
                context.bot.restrict_chat_member(chat_id=chat_id, user_id=user.id, permissions=permissions, until_date=until_date)
                message.reply_text(f"{user.first_name} has been muted for 3 days.")
                return

        # Check for delete phrases
        for phrase in DELETE_PHRASES:
            if phrase in message_text:
                print(f"[DELETE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                return
            
    # Filter Responses (apply to all)
    for trigger, filter_data in FILTERS.items():
            if trigger in message_text:
                print(f"[FILTER MATCH] Trigger: '{trigger}'")

                response_text = filter_data.get("response_text", "")
                media_file = filter_data.get("media")
                media_type = filter_data.get("type", "gif").lower()  # Default to gif if not specified

                if media_file:
                    media_path = os.path.join(MEDIA_FOLDER, media_file)

                    if os.path.exists(media_path):
                        if media_type == "gif" or media_type == "animation":
                            context.bot.send_animation(chat_id=chat_id, animation=open(media_path, 'rb'), caption=response_text)
                        elif media_type == "image":
                            context.bot.send_photo(chat_id=chat_id, photo=open(media_path, 'rb'), caption=response_text)
                        elif media_type == "video":
                            context.bot.send_video(chat_id=chat_id, video=open(media_path, 'rb'), caption=response_text)
                        else:
                            print(f"[WARN] Unknown media type '{media_type}' for trigger '{trigger}'")
                    else:
                        print(f"[ERROR] Media file '{media_path}' not found.")
                        message.reply_text(response_text)

                else:
                    message.reply_text(response_text)

                return  # Only respond to first matched filter

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
