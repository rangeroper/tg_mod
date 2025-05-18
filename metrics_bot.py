import os
import json
import subprocess
from dotenv import load_dotenv
from telegram import Bot
from api.telegram import get_telegram_stats
from api.holders import get_token_stats
from api.github import get_github_stats

# from api.followers import get_x_followers_stats

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv("GROUP_CHAT_ID")

bot = Bot(token=BOT_TOKEN)

def send_update_to_tg(messages):
    """Sends a combined update message to the Telegram group."""
    full_message = "\n\n".join(messages)
    bot.send_message(chat_id=CHAT_ID, text=full_message)
    return full_message

def save_last_metrics_message_as_filter(message):
    """Save the last sent message to /filters/metrics.json, overwriting previous content."""
    os.makedirs("filters", exist_ok=True)
    data = {"last_metrics_message": message}
    with open("filters/metrics.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def commit_metrics_changes():
    status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if status.stdout.strip():
        print("Git status shows changes, committing now...")
        
        add_result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
        print(f"git add output:\n{add_result.stdout}\n{add_result.stderr}")
        
        commit_result = subprocess.run(['git', 'commit', '-m', 'Automated metrics update'], capture_output=True, text=True)
        print(f"git commit output:\n{commit_result.stdout}\n{commit_result.stderr}")
        
        push_result = subprocess.run(['git', 'push'], capture_output=True, text=True)
        print(f"git push output:\n{push_result.stdout}\n{push_result.stderr}")
    else:
        print("No changes to commit.")

def main():
    # Telegram Metrics
    telegram_message = get_telegram_stats()
        
    # GitHub Metrics
    github_stats = get_github_stats()

    # Holders Metrics
    token_stats = get_token_stats()

    # Followers Metrics
    # x_followers_stats = get_x_followers_stats()

    # Create a list of messages
    messages = [
        github_stats,
        telegram_message,
        token_stats,
        # x_followers_stats
    ]

    # Send all metrics together in one message
    full_message = send_update_to_tg(messages)
    save_last_metrics_message_as_filter(full_message)
    commit_metrics_changes()

if __name__ == "__main__":
    main()
