import os
from dotenv import load_dotenv
from telegram import Update, ParseMode, Bot
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext


# Load .env variables
load_dotenv()

# Bot token and group chat ID
MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# separate instance of bot using the main group chat bot
main_bot = Bot(token=BOT_TOKEN)

def debug_all_updates(update: Update, context: CallbackContext):
    print("Received raw update:")
    print(update)

def handle_say_command(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        print("No message or channel post detected in middleware group.")
        return

    message_text = message.text or ""

    if message_text.lower().startswith('/say '):
        say_message = message_text[5:].strip()

        if say_message:
            try:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
            except Exception as e:
                print(f"Failed to delete /say command in middleware: {e}")

            try:
                main_bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=say_message,
                    parse_mode=ParseMode.HTML
                )
                print(f"Relayed /say from middleware to main group: {say_message}")
            except Exception as e:
                print(f"Failed to send message to main group: {e}")
        else:
            print("Empty /say command in middleware, skipping.")

def handle_buy_bot_notifications(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        print("No message or channel post detected in middleware group.")
        return

    # Ensure the message is from @delugebuybot or display name "D.BuyBot"
    if not message.from_user:
        print("Message has no sender, skipping.")
        return

    username = message.from_user.username or ""
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()

    if username.lower() != "delugebuybot" and full_name != "D.BuyBot":
        print(f"Message is not from @delugebuybot or name 'D.BuyBot' (username: {username}, full name: {full_name}), skipping.")
        return

    message_text = message.text or ""
    print(f"Received buy bot notification: {message_text}")

    if message_text.strip():
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete buy bot message in middleware: {e}")

        try:
            main_bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=message_text,
                parse_mode=ParseMode.HTML
            )
            print("Forwarded buy bot notification to main group.")
        except Exception as e:
            print(f"Failed to send buy bot notification to main group: {e}")
    else:
        print("Empty buy bot message detected, skipping.")


def main():
    print("Starting middleware listener bot...")
    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(MessageHandler(Filters.all, debug_all_updates))
    dp.add_handler(MessageHandler(Filters.all, handle_say_command))
    dp.add_handler(MessageHandler(Filters.all, handle_buy_bot_notifications))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
