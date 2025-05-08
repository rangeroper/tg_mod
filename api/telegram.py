import os
import json
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def get_telegram_stats():
    """Fetches Telegram group statistics and computes percentage increases."""
    # Load previous stats
    previous_count = load_previous_count()
    
    try:
        # Get current member count
        current_count = await bot.get_chat_member_count(GROUP_CHAT_ID)
        
        # Calculate increase and percentage change
        if previous_count == 0:
            increase = current_count
            percent_change = 100 if current_count > 0 else 0
        else:
            increase = current_count - previous_count
            percent_change = (increase / previous_count * 100) if previous_count else 0
        
        # Save the current count for future comparisons
        save_current_count(current_count)
        
        # Format current_count with commas
        formatted_count = "{:,}".format(current_count)
        
        # Format the stats into a message
        message = f"👥 Telegram Members  >>  {formatted_count} ({percent_change:.2f}%)"
        
        return message
    except Exception as e:
        print(f"Error fetching Telegram stats: {e}")
        return "❌ Error fetching Telegram member count."

def load_previous_count():
    """Loads previous count from file or returns 0 if the file is missing or invalid."""
    if os.path.exists("data/telegram_metrics.json"):
        with open("data/telegram_metrics.json", "r") as f:
            try:
                data = json.load(f)
                return data.get("count", 0)
            except json.JSONDecodeError:
                return 0
    else:
        return 0

def save_current_count(count):
    """Saves the current count to file, creating the file if it doesn't exist."""
    with open("data/telegram_metrics.json", "w") as f:
        json.dump({"count": count}, f)