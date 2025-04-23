import os
from dotenv import load_dotenv
from telegram import Update, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from datetime import timedelta
import re
import json

load_dotenv()  # Load .env vars

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# File path for filters
FILTERS_FILE = "filters/filters.json"

# File path for accompanying filter media
MEDIA_FOLDER = "media"

# File paths for phrases
BAN_PHRASES_FILE = "blocklists/ban_phrases.txt"
MUTE_PHRASES_FILE = "blocklists/mute_phrases.txt"
DELETE_PHRASES = "blocklists/delete_phrases.txt"

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

# Suspicious names to auto-ban
SUSPICIOUS_USERNAMES = [
    "dev", "developer", "admin", "mod", "owner", "arc", "arc_agent", "arc agent", "support", "helpdesk"
]

def contains_multiplication_phrase(text):
    text = text.lower()
    pattern = r"\b(?:[1-9][0-9]{0,3}|10000)\s*x\s*|\bx\s*(?:[1-9][0-9]{0,3}|10000)\b"
    return re.search(pattern, text)

def check_message(update: Update, context: CallbackContext):
    print(f"[DEBUG] Chat ID: {update.effective_chat.id}")

def check_message(update: Update, context: CallbackContext):
    message = update.message or update.channel_post  # Handle both messages and channel posts
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = update.effective_user

    if not message or not message.text:
        return  # Skip non-text or unsupported messages
    
    message_text = message.text.lower()

    # Log incoming message (for debugging)
    print(f"[DEBUG] Received message from {user.first_name} (ID: {user_id}) in Chat ID: {chat_id}")
    print(f"[DEBUG] Message text: '{message_text}'")

    # Fetch chat admins to prevent acting on their messages
    chat_admins = context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in chat_admins]

    # Auto-ban based on suspicious name or username
    name_username = f"{user.full_name} {user.username or ''}".lower()
    
    if any(keyword in name_username for keyword in SUSPICIOUS_USERNAMES):
        context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        return

    # Check for multiplication spam
    if contains_multiplication_phrase(message_text):
        context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        return

    if user_id not in admin_ids:
        if len(message_text.strip()) < 2:
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return

        for phrase in BAN_PHRASES:
            if phrase in message_text:
                print(f"[BAN MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                message.reply_text(f"arc angel fallen. {user.first_name} has been banned.")
                return

        for phrase in MUTE_PHRASES:
            if phrase in message_text:
                print(f"[MUTE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                until_date = message.date + timedelta(seconds=MUTE_DURATION)
                permissions = ChatPermissions(can_send_messages=False)
                context.bot.restrict_chat_member(chat_id=chat_id, user_id=user.id, permissions=permissions, until_date=until_date)
                message.reply_text(f"{user.first_name} has been muted for 3 days.")
                return

        for phrase in DELETE_PHRASES:
            if phrase in message_text:
                print(f"[DELETE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                return

    # Filter Responses (apply to all)
    for trigger, filter_data in FILTERS.items():
        normalized_trigger = trigger.strip().lower()
        if normalized_trigger in message_text:
            response_text = filter_data.get("response_text", "")
            media_file = filter_data.get("media")
            media_type = filter_data.get("type", "gif").lower()

            if media_file:
                media_path = os.path.join(MEDIA_FOLDER, media_file)
                if os.path.exists(media_path):
                    with open(media_path, 'rb') as media:
                        if media_type in ["gif", "animation"]:
                            context.bot.send_animation(chat_id=chat_id, animation=media, caption=response_text or None)
                        elif media_type == "image":
                            context.bot.send_photo(chat_id=chat_id, photo=media, caption=response_text or None)
                        elif media_type == "video":
                            context.bot.send_video(chat_id=chat_id, video=media, caption=response_text or None)
                elif response_text:
                    message.reply_text(response_text)
            elif response_text:
                message.reply_text(response_text)
            return  # Respond only once

        
def list_filters(update: Update, context: CallbackContext):
    # Load the latest filters
    with open(FILTERS_FILE, 'r', encoding='utf-8') as f:
        filters = json.load(f)

    # Get and sort all triggers alphabetically (removing leading slash only for sorting)
    sorted_triggers = sorted(filters.keys(), key=lambda k: k.lstrip('/').lower())

    # Re-apply slash only if the original trigger had it
    formatted_triggers = [f"`{trigger}`" for trigger in sorted_triggers]

    # Telegram messages max out at 4096 characters
    response = "*Available Filters:*\n" + "\n".join(formatted_triggers)
    if len(response) > 4000:
        for i in range(0, len(formatted_triggers), 80):  # 80 items per message chunk
            chunk = "*Available Filters:*\n" + "\n".join(formatted_triggers[i:i+80])
            update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        update.message.reply_text(response, parse_mode="Markdown")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # output filters
    dp.add_handler(CommandHandler("filters", list_filters))

    # Add text and command message handler
    dp.add_handler(MessageHandler(Filters.text | Filters.command, check_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
