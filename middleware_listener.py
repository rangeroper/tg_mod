import os
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters

# Load environment variables from the .env file
load_dotenv()

# Fetch environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MIDDLEWARE_CHAT_ID = int(os.getenv("MIDDLEWARE_CHAT_ID"))

# Function to check messages in the middleware group
def check_middleware_message(update, context):
    if update.message.chat.id == MIDDLEWARE_CHAT_ID:
        print(f"Message from middleware group: {update.message.text}")

def main():
    # Initialize the Updater with the bot token
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Set up a handler for all text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_middleware_message))

    # Start polling for updates
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
