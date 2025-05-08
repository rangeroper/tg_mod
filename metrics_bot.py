# bot.py
import asyncio
import os
from api.telegram import get_telegram_stats
from api.github import get_github_stats
from api.holders import get_token_stats
from api.followers import get_x_followers_stats
from telegram import Bot

# Initialize bot using Config
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv("GROUP_CHAT_ID")

bot = Bot(token=BOT_TOKEN)

async def send_update_to_tg(messages):
    """Sends a combined update message to the Telegram group."""
    full_message = "\n\n".join(messages)
    await bot.send_message(chat_id=CHAT_ID, text=full_message)

async def main():
    # Telegram Metrics
    telegram_message = await get_telegram_stats()  
        
    # GitHub Metrics
    github_stats = await get_github_stats()  

    # Holders Metrics
    token_stats = await get_token_stats()

    # Followers Metrics
    x_followers_stats = await get_x_followers_stats()

    # Create a list of messages
    messages = [
        github_stats,
        telegram_message,       
        token_stats,
        x_followers_stats        
    ]
    
    # Send all metrics together in one message
    await send_update_to_tg(messages)

if __name__ == "__main__":
    # Use asyncio.run() to start the async main function
    asyncio.run(main())