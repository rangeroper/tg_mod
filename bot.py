import os
from dotenv import load_dotenv
from telegram import Update, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from datetime import timedelta
import re

load_dotenv()  # Load .env vars

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# File paths for phrases
BAN_PHRASES_FILE = "ban_phrases.txt"
MUTE_PHRASES_FILE = "mute_phrases.txt"
DELETE_PHRASES = "delete_phrases.txt"

# Mute duration in seconds (3 days)
MUTE_DURATION = 3 * 24 * 60 * 60

def load_phrases(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip().lower() for line in file.readlines()]

# Load phrases from files
BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES)

def check_message(update: Update, context: CallbackContext):
    print(f"[DEBUG] Chat ID: {update.effective_chat.id}")

def check_message(update: Update, context: CallbackContext):
    message = update.message or update.channel_post  # Handle both
    chat_id = update.effective_chat.id  # Dynamically get the chat ID
    user_id = update.effective_user.id  # Get the user ID of the person sending the message

    # Fetch the list of admins in the chat
    chat_admins = context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in chat_admins]

    # Prevent the bot from acting on the owner's and admins' messages
    if user_id in admin_ids:
        print("[DEBUG] Skipping action for an admin or owner.")
        return  # Do nothing if the message is from an admin or the owner

    print(f"[DEBUG] Received message in chat ID: {chat_id}")
    print(f"[DEBUG] message.text: {getattr(message, 'text', None)}")

    if not message or not message.text:
        return  # Skip non-text or unsupported updates

    message_text = message.text.lower()
    user = update.effective_user

    # Check for ban phrases
    for phrase in BAN_PHRASES:
        pattern = rf'\b{re.escape(phrase)}\b'
        if re.search(pattern, message_text):
            context.bot.kick_chat_member(chat_id=chat_id, user_id=user.id)
            message.reply_text(f"arc angel fallen. {user.first_name} has been banned.")
            return

    # Check for mute phrases
    for phrase in MUTE_PHRASES:
        pattern = rf'\b{re.escape(phrase)}\b'
        if re.search(pattern, message_text):
            until_date = message.date + timedelta(seconds=MUTE_DURATION)
            permissions = ChatPermissions(can_send_messages=False)
            context.bot.restrict_chat_member(chat_id=chat_id, user_id=user.id, permissions=permissions, until_date=until_date)
            message.reply_text(f"{user.first_name} has been muted for 3 days.")
            return
        
    # Check for delete phrases
    for phrase in DELETE_PHRASES:
        pattern = rf'\b{re.escape(phrase)}\b'
        if re.search(pattern, message_text):
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
