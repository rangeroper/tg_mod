import sys
from pathlib import Path
import os
import json
import asyncio
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from telegram import Bot
from api.telegram import get_telegram_stats
from api.holders import get_token_stats
from api.github import get_github_stats
from api.followers import get_x_followers_stats

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv("GROUP_CHAT_ID")

bot = Bot(token=BOT_TOKEN)

def send_update_to_tg(messages):
    """Sends a combined update message to the Telegram group."""
    full_message = "\n\n".join(messages)
    try:
        bot.send_message(chat_id=CHAT_ID, text=full_message)
    except Exception as e:
        print(f"Failed to send message to Telegram: {e}")
    return full_message

def save_last_metrics_message_as_filter(message):
    """Save the last sent message to /filters/metrics.json, overwriting previous content."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    filters_dir = os.path.join(project_root, "filters")
    os.makedirs(filters_dir, exist_ok=True)

    data = {"last_metrics_message": message}
    metrics_path = os.path.join(filters_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

async def main():
    # Telegram Metrics (sync)
    telegram_message = get_telegram_stats()
        
    # GitHub Metrics (sync)
    github_stats = get_github_stats()

    # Holders Metrics (sync)
    token_stats = get_token_stats()

    # Followers Metrics (async, so await it)
    x_followers_stats = await get_x_followers_stats()

    x_followers_message = x_followers_stats.get("data", {}).get("message", str(x_followers_stats))

    # Create a list of messages
    messages = [
        github_stats,
        telegram_message,
        token_stats,
        x_followers_message
    ]

    # Send all metrics together in one message
    full_message = send_update_to_tg(messages)
    save_last_metrics_message_as_filter(full_message)

if __name__ == "__main__":
    asyncio.run(main())
