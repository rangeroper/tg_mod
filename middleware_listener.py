import os
import re
from dotenv import load_dotenv
from telegram import Update, ParseMode, Bot
from telegram.ext import TypeHandler, Updater, MessageHandler, Filters, CallbackContext, CommandHandler

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
    print("⚠️ RAW UPDATE:", update)

    message = (
        update.message
        or update.edited_message
        or update.channel_post
        or update.edited_channel_post
    )

    if not message:
        print("❌ No message found in update.")
        return

    if hasattr(message, "is_automatic_forward") and message.is_automatic_forward:
        print("✅ Detected automatic forward (likely from Deluge)")
        print("Text:", message.text)
        print("Caption:", message.caption)
        print("Forwarded From Chat:", message.forward_from_chat)

    user = message.from_user
    chat = message.chat

    log_data = {
        "chat_id": chat.id,
        "chat_type": chat.type,
        "chat_title": chat.title or chat.username,
        "message_id": message.message_id,
        "from_user_id": user.id if user else "N/A",
        "from_username": user.username if user else "N/A",
        "from_first_name": user.first_name if user else "N/A",
        "from_last_name": user.last_name if user else "N/A",
        "from_is_bot": user.is_bot if user else "N/A",
        "date": message.date.isoformat(),
        "text": (
            message.text
            or message.caption
            or (message.forward_from_chat.title if message.forward_from_chat else None)
            or "<NO TEXT>"
        ),
        "has_photo": bool(message.photo),
        "has_video": bool(message.video),
        "has_document": bool(message.document),
        "has_audio": bool(message.audio),
        "has_voice": bool(message.voice),
        "has_sticker": bool(message.sticker),
        "has_location": bool(message.location),
        "has_venue": bool(message.venue),
        "has_poll": bool(message.poll),
        "has_contact": bool(message.contact),
        "has_game": bool(message.game),
        "forwarded_from_user": (
            f"{message.forward_from.full_name} ({message.forward_from.username})"
            if message.forward_from else None
        ),
        "forwarded_from_chat": (
            f"{message.forward_from_chat.title or message.forward_from_chat.username}"
            if message.forward_from_chat else None
        ),
        "forward_signature": message.forward_signature or None,
        "is_automatic_forward": getattr(message, "is_automatic_forward", False),
        "edit_date": message.edit_date.isoformat() if message.edit_date else None,
    }

    print("-------- New Message --------")
    for k, v in log_data.items():
        print(f"{k}: {v}")
    print("-----------------------------")

    print("🔍 Message Attributes:")
    for attr in dir(message):
        if not attr.startswith("_"):
            try:
                print(f"{attr}: {getattr(message, attr)}")
            except Exception as e:
                print(f"{attr}: [Error reading attribute] {e}")

def main():
    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.regex('^/say '), handle_say_command))
    dp.add_handler(TypeHandler(Update, log_everything), group=999)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()