import os

from dotenv import load_dotenv

load_dotenv()

MIDDLEWARE_CHAT_ID = int(os.getenv("MIDDLEWARE_CHAT_ID"))

def check_middleware_message(update, context):
    print(f"[ANY MESSAGE] From chat ID: {update.message.chat.id}, text: {update.message.text}")
    if update.message.chat.id == MIDDLEWARE_CHAT_ID:
        print(f"[MIDDLEWARE GROUP] {update.message.text}")
