import os
import re
from dotenv import load_dotenv
from telegram import Update, ParseMode, Bot
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

# Load .env variables
load_dotenv()

# Bot token and group chat ID
MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# Separate instance of bot using the main group chat bot
main_bot = Bot(token=BOT_TOKEN)

def is_deluge_buy_bot_message(message):
    if not message or not (message.text or message.caption):
        return False
    
    # Get the text content from either text or caption
    content = message.text or message.caption or ""
    
    # Common patterns in Deluge buy bot messages
    deluge_patterns = [
        r"Buy!",                     # Buy indicator
        r"\(https://t\.me/\+[\w\d]+\)",  # Telegram invite link
        r"🔀 \d+\.?\d* (SOL|ETH|BTC)",   # Transaction amount format
        r"👤 [\w\d]+\.{3}[\w\d]+",       # Wallet address shortened format
        r"Position: \d+\.?\d*% Up!",     # Position up indicator
        r"Market Cap \$[\d,]+",          # Market cap format
        r"⚪️🙂",                         # Emoji pattern seen in the messages
        r"Chart \(https://",             # Chart link
        r"Txn \(https://",               # Transaction link
        r"⬆️ Position",                  # Position up indicator with emoji
        r"💸 Market Cap",                # Market cap with emoji
        r"📈 Chart"                      # Chart with emoji
    ]
    
    # Check if the sender is the buy bot (if sender info is available)
    sender_is_buy_bot = False
    if message.from_user:
        username = message.from_user.username or ""
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        sender_is_buy_bot = username.lower() == "delugebuybot" or "buybot" in full_name.lower()
    
    # Check if the message matches patterns from Deluge Buy Bot
    pattern_matches = sum(1 for pattern in deluge_patterns if re.search(pattern, content)) >= 2
    
    # If forwarded from a channel, check channel name
    channel_is_buy_bot = False
    if message.forward_from_chat:
        channel_title = message.forward_from_chat.title or ""
        channel_is_buy_bot = "deluge" in channel_title.lower() or "buy bot" in channel_title.lower()
    
    return sender_is_buy_bot or pattern_matches or channel_is_buy_bot

def handle_say_command(update: Update, context: CallbackContext):
    """Handle /say commands to relay messages to the main group"""
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

# def handle_all_messages(update: Update, context: CallbackContext):
#     message = update.message or update.channel_post
#     if not message:
#         print(f"not a message: {e}")
#         return

#     if is_deluge_buy_bot_message(message):
#         message_text = message.text or message.caption or ""
#         if message_text.strip():
#             try:
#                 context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
#             except Exception as e:
#                 print(f"Failed to delete Deluge-style message: {e}")

#             try:
#                 main_bot.send_message(
#                     chat_id=GROUP_CHAT_ID,
#                     text=message_text,
#                     parse_mode=ParseMode.HTML
#                 )
#                 print(f"Forwarded Deluge buy bot message: {message_text}")
#             except Exception as e:
#                 print(f"Failed to forward Deluge-style message: {e}")

def log_everything(update: Update, context: CallbackContext):
    message = (
        update.message
        or update.edited_message
        or update.channel_post
        or update.edited_channel_post
    )

    if not message:
        print("No message to log.")
        return

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
        "text": message.text or message.caption or None,
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
        "is_automatic_forward": message.is_automatic_forward if hasattr(message, "is_automatic_forward") else False,
        "edit_date": message.edit_date.isoformat() if message.edit_date else None,
    }

    print("-------- New Message --------")
    for k, v in log_data.items():
        print(f"{k}: {v}")
    print("-----------------------------")


def main():
    print("Starting middleware listener bot...")
    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.regex('^/say '), handle_say_command))
    dp.add_handler(MessageHandler(Filters.all, log_everything), group=0)
    # dp.add_handler(MessageHandler(Filters.all, handle_all_messages))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()