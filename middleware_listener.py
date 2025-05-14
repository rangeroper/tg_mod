import os
import re
from dotenv import load_dotenv
from telegram import Update, ParseMode, Bot
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# Load .env variables
load_dotenv()

# Bot token and group chat ID
MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# Separate instance of bot using the main group chat bot
main_bot = Bot(token=BOT_TOKEN)

def handle_say_command(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        return

    message_text = message.text or ""
    say_message = ""

    if message_text.lower().startswith('/say '):
        say_message = message_text[5:].strip()

    if say_message:
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete /say command: {e}")

        try:
            main_bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=say_message,
                parse_mode=ParseMode.HTML
            )
            print(f"Relayed /say command: {say_message}")
        except Exception as e:
            print(f"Failed to send /say message to main group: {e}")

def log_everything(update: Update, context: CallbackContext):
    message = update.message or update.edited_message or update.channel_post or update.edited_channel_post
    if not message:
        return
    
    is_forwarded = hasattr(message, 'forward_from') or hasattr(message, 'forward_from_chat')
    is_automatic_forward = hasattr(message, 'is_automatic_forward') and message.is_automatic_forward

    # Log simple message details (forwarded or not)
    log_data = {
        "chat_id": message.chat.id,
        "message_id": message.message_id,
        "from_user_id": message.from_user.id if message.from_user else "N/A",
        "text": message.text or "<No Text>",
        "is_forwarded": "Yes" if is_forwarded else "No",
        "is_automatic_forward": "Yes" if is_automatic_forward else "No",
        "has_photo": bool(message.photo),
        "has_video": bool(message.video),
        "has_document": bool(message.document),
        "has_audio": bool(message.audio),
        "has_voice": bool(message.voice),
        "has_sticker": bool(message.sticker),
        "has_location": bool(message.location),
    }

    # Just print out the key attributes
    print("Message received:")
    for key, value in log_data.items():
        print(f"{key}: {value}")

def main():
    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.regex('^/say '), handle_say_command))
    dp.add_handler(MessageHandler(Filters.all, log_everything))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()