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

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

def log_message(message):
    """Helper function to log messages when DEBUG is True"""
    if DEBUG:
        print(message)

def is_deluge_buy_bot_message(message):
    """
    Check if a message is from the Deluge Buy Bot based on content patterns
    """
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
        log_message("No message or channel post detected in middleware group.")
        return

    message_text = message.text or ""

    if message_text.lower().startswith('/say '):
        say_message = message_text[5:].strip()

        if say_message:
            try:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
            except Exception as e:
                log_message(f"Failed to delete /say command in middleware: {e}")

            try:
                main_bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=say_message,
                    parse_mode=ParseMode.HTML
                )
                log_message(f"Relayed /say from middleware to main group: {say_message}")
            except Exception as e:
                log_message(f"Failed to send message to main group: {e}")
        else:
            log_message("Empty /say command in middleware, skipping.")

def handle_all_messages(update: Update, context: CallbackContext):
    """Process all messages to detect and forward buy bot notifications"""
    message = update.message or update.channel_post
    if not message:
        log_message("No message or channel post detected.")
        return

    # Log message details for debugging
    if DEBUG:
        sender_info = "Unknown sender"
        if message.from_user:
            sender_info = f"@{message.from_user.username or ''} ({message.from_user.first_name or ''} {message.from_user.last_name or ''})"
        elif message.forward_from_chat:
            sender_info = f"Channel: {message.forward_from_chat.title or ''}"
        
        log_message(f"Received message from {sender_info}")
        log_message(f"Content: {message.text or message.caption or 'No text'}")
    
    # Check if it's a buy bot notification
    if is_deluge_buy_bot_message(message):
        message_text = message.text or message.caption or ""
        log_message(f"Detected buy bot notification: {message_text}")

        if message_text.strip():
            try:
                # Try to delete the original message from middleware chat
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
            except Exception as e:
                log_message(f"Failed to delete buy bot message in middleware: {e}")

            try:
                # Forward to main group
                main_bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=message_text,
                    parse_mode=ParseMode.HTML
                )
                log_message("Forwarded buy bot notification to main group.")
            except Exception as e:
                log_message(f"Failed to send buy bot notification to main group: {e}")
        else:
            log_message("Empty buy bot message detected, skipping.")

def debug_command(update: Update, context: CallbackContext):
    """Command to toggle debug mode"""
    global DEBUG
    DEBUG = not DEBUG
    update.message.reply_text(f"Debug mode is now {'ON' if DEBUG else 'OFF'}")

def status_command(update: Update, context: CallbackContext):
    """Report bot status"""
    update.message.reply_text(
        f"Middleware Bot is running\n"
        f"Debug mode: {'ON' if DEBUG else 'OFF'}\n"
        f"Configured to forward to chat ID: {GROUP_CHAT_ID}"
    )

def main():
    print("Starting middleware listener bot...")
    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add command handlers
    dp.add_handler(CommandHandler("debug", debug_command))
    dp.add_handler(CommandHandler("status", status_command))
    
    # Add message handlers
    dp.add_handler(MessageHandler(Filters.regex('^/say '), handle_say_command))
    
    # This should be the last handler as it will catch all messages
    dp.add_handler(MessageHandler(Filters.all, handle_all_messages))

    updater.start_polling()
    print("Bot is now listening for messages...")
    updater.idle()

if __name__ == '__main__':
    main()