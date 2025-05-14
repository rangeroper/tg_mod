import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telegram import Bot, ParseMode

# Load .env variables
load_dotenv()

# Bot token and group chat ID
MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
TG_API_ID=os.getenv('TG_API_ID')
TG_API_HASH=os.getenv('TG_API_HASH')

client = TelegramClient('bot', TG_API_ID, TG_API_HASH).start(bot_token=MIDDLEWARE_BOT_TOKEN)

# separate instance of bot using the main group chat bot
main_bot = Bot(token=BOT_TOKEN)

# Handle '/say' commands in the middleware chat
async def handle_say_command(message):
    if message.text and message.text.lower().startswith('/say '):
        say_message = message.text[5:].strip()
        
        if say_message:
            try:
                await message.delete()
            except Exception as e:
                print(f"Failed to delete /say command in middleware: {e}")

            try:
                # Forward message to the main group
                await main_bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=say_message,
                    parse_mode=ParseMode.HTML
                )
                print(f"Relayed /say from middleware to main group: {say_message}")
            except Exception as e:
                print(f"Failed to send message to main group: {e}")
        else:
            print("Empty /say command in middleware, skipping.")

async def handle_buy_bot_notifications(message):
    # Ensure the message is from @delugebuybot or display name "D.BuyBot"
    if message.sender.username == "delugebuybot" or message.sender.first_name == "D.BuyBot":
        message_text = message.text or ""
        print(f"Received buy bot notification: {message_text}")

        if message_text.strip():
            try:
                await message.delete()
            except Exception as e:
                print(f"Failed to delete buy bot message in middleware: {e}")

            try:
                # Forward buy bot message to the main group
                await main_bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=message_text,
                    parse_mode=ParseMode.HTML
                )
                print("Forwarded buy bot notification to main group.")
            except Exception as e:
                print(f"Failed to send buy bot notification to main group: {e}")
        else:
            print("Empty buy bot message detected, skipping.")

@client.on(events.NewMessage)
async def message_handler(event):
    message = event.message

    # Handle '/say' command
    if message.text and message.text.lower().startswith('/say '):
        await handle_say_command(message)

    # Handle buy bot notifications
    elif message.sender and (message.sender.username == "delugebuybot" or message.sender.first_name == "D.BuyBot"):
        await handle_buy_bot_notifications(message)

def main():
    print("Starting middleware listener bot...")
    # Start the Telethon client
    client.start()
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
