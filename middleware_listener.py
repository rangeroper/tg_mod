import os
from dotenv import load_dotenv
from telegram import ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, Update

# Load .env variables
load_dotenv()

# Bot token and group chat ID
MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# Function to handle /say messages in middleware
def check_middleware_message(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        print("No message or channel post detected in middleware group.")
        return

    message_text = message.text or ""

    # Check if the message starts with '/say'
    if message_text.lower().startswith('/say '):
        say_message = message_text[5:].strip()  # Remove "/say " from message output

        if say_message:
            try:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
            except Exception as e:
                print(f"Failed to delete /say command in middleware: {e}")

            try:
                context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=say_message,
                    parse_mode=ParseMode.HTML
                )
                print(f"Relayed /say from middleware to main group: {say_message}")
            except Exception as e:
                print(f"Failed to send message to main group: {e}")
        else:
            print("Empty /say command in middleware, skipping.")

# Handle Buy Bot Notifications
def check_other_messages(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        print("No message or channel post detected.")
        return

    message_text = message.text or ""

    print(f"Received buy bot notification: {message_text}")

def main():
    print("Starting middleware listener bot...")
    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & Filters.regex('^/say '), check_middleware_message))
    dp.add_handler(MessageHandler(Filters.text, check_other_messages))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
