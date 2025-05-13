import os
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters

# Load .env variables
load_dotenv()

# Bot token and middleware group ID
BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
MIDDLEWARE_CHAT_ID = int(os.getenv("MIDDLEWARE_CHAT_ID"))

# Message handler function
def handle_middleware_message(update, context):
    if update.message.chat.id == MIDDLEWARE_CHAT_ID:
        print(f"[MIDDLEWARE MESSAGE] {update.message.text}")

# Start the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Only handle messages from the middleware group
    dp.add_handler(MessageHandler(Filters.chat(chat_id=MIDDLEWARE_CHAT_ID), handle_middleware_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
