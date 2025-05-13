import os

from dotenv import load_dotenv

load_dotenv()

MIDDLEWARE_CHAT_ID = int(os.getenv("MIDDLEWARE_CHAT_ID"))

def check_middleware_message(update, context):
    if update.message.chat.id == MIDDLEWARE_CHAT_ID:
        print(f"[MIDDLEWARE GROUP] {update.message.text}")
