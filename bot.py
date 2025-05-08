import os
import re
import json
import subprocess
from dotenv import load_dotenv
from telegram import Update, ChatPermissions, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, CallbackQueryHandler
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone, time
from combot.scheduled_warnings import messages
from combot.brand_assets import messages as brand_assets_messages

load_dotenv()  # Load .env vars

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# File path for filters
FILTERS_FILE = "filters/filters.json"

# File path for accompanying filter media
MEDIA_FOLDER = "media"

# File paths for phrases
BAN_PHRASES_FILE = "blocklists/ban_phrases.txt"
MUTE_PHRASES_FILE = "blocklists/mute_phrases.txt"
DELETE_PHRASES_FILE = "blocklists/delete_phrases.txt"
WHITELIST_PHRASES_FILE = "whitelists/whitelist_phrases.txt"

# Suspicious names to auto-ban
SUSPICIOUS_USERNAMES = [
    "dev", "developer", "admin", "mod", "owner", "arc", "arc_agent", "arc agent", "arch_agent", "arch agent", "support", "helpdesk", "administrator", "arc admin", "arc_admin"
]

# Mute duration in seconds (3 days)
MUTE_DURATION = 3 * 24 * 60 * 60

# auto spam detection variables
SPAM_THRESHOLD = 3
TIME_WINDOW = timedelta(seconds=15)
SPAM_TRACKER = defaultdict(lambda: deque(maxlen=SPAM_THRESHOLD))
SPAM_RECORDS = {} # stores flagged spam messages for 5 minutes
SPAM_RECORD_DURATION = timedelta(minutes=5)

def get_admin_ids(context, chat_id):
    # Fetch chat admins dynamically
    chat_admins = context.bot.get_chat_administrators(chat_id)
    return [admin.user.id for admin in chat_admins]

# combot security message
def post_security_message(context: CallbackContext, index: int):
    try:
        chat = context.bot.get_chat(GROUP_CHAT_ID)
        pinned = chat.pinned_message
        if pinned:
            try:
                context.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Security] Failed to unpin message: {e}")
            try:
                context.bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Security] Failed to delete message: {e}")
    except Exception as e:
        print(f"[Security] Failed to retrieve chat or pinned message: {e}")
    try:
        message = messages[index]
        sent_message = context.bot.send_message(
            chat_id=GROUP_CHAT_ID, 
            text=message, 
            parse_mode=ParseMode.HTML
        )
        context.bot.pin_chat_message(
            chat_id=GROUP_CHAT_ID, 
            message_id=sent_message.message_id, 
            disable_notification=True
        )
    except Exception as e:
        print(f"[Security] Failed to pin message: {e}")

# combot brand assets
def post_brand_assets(context: CallbackContext, index: int = 0):
    try:
        chat = context.bot.get_chat(GROUP_CHAT_ID)
        pinned = chat.pinned_message
        if pinned:
            try:
                context.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Brand Assets] Failed to unpin message: {e}")
            try:
                context.bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Brand Assets] Failed to delete message: {e}")
    except Exception as e:
        print(f"[Brand Assets] Failed to retrieve chat or pinned message: {e}")
    try:
        message = brand_assets_messages[index]
        sent_message = context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )
        context.bot.pin_chat_message(
            chat_id=GROUP_CHAT_ID,
            message_id=sent_message.message_id,
            disable_notification=True
        )
    except Exception as e:
        print(f"[Brand Assets] Failed to send or pin message: {e}")

# Load filters as dict
def load_filters(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

FILTERS = load_filters(FILTERS_FILE)

# Load blocklist/whitelisted words/phrases from files
def load_phrases(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip().lower() for line in file.readlines()]

BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES_FILE)
WHITELIST_PHRASES = load_phrases(WHITELIST_PHRASES_FILE)

def contains_multiplication_phrase(text):
    text = text.lower()
    # Match digit(s) possibly separated by spaces, next to an 'x'
    pattern = r"(?:\d\s*)+x|x\s*(?:\d\s*)+"
    return re.search(pattern, text)

def contains_give_sol_phrase(text):
    text = text.lower()
    # Match 'give' followed by a number and then 'sol' or 'solana'
    pattern = r"give\s*(\d+)\s*(sol|solana)"
    return re.search(pattern, text)

# check for spam
def check_for_spam(message_text, user_id):
    now = datetime.now(timezone.utc)
    # track user and timestamp of the message
    print(f"Checking for spam: {message_text} from user: {user_id}")
    SPAM_TRACKER[message_text].append((user_id, now))

    # Filter out old messages that are outside of the time window
    recent = [entry for entry in SPAM_TRACKER[message_text] if now - entry[1] <= TIME_WINDOW]
    SPAM_TRACKER[message_text] = deque(recent)

    print(f"Recent messages for '{message_text}': {recent}")

    # If recent messages exceed the threshold, flag as spam
    if len(recent) >= SPAM_THRESHOLD:
        print(f"Spam detected for message: '{message_text}'")
        # flag message as spam and store for 5 minutes in memory
        SPAM_RECORDS[message_text] = now # only store message and timestamp
        spammer_ids = list(set([entry[0] for entry in recent])) # Return list of user_ids to mute
        print(f"Flagging {len(spammer_ids)} users for spam: {spammer_ids}") 
        return spammer_ids
    
    elif recent and len(recent) < SPAM_THRESHOLD and (now - recent[0][1] > TIME_WINDOW):
        # Not spam, expired window – clean it up
        SPAM_TRACKER.pop(message_text, None)

    return []

# check for recent spam and mute spammers
def check_recent_spam(message_text):
    now = datetime.now(timezone.utc)
    timestamp = SPAM_RECORDS.get(message_text)
    if timestamp:
        print(f"Message '{message_text}' is flagged as spam, timestamp: {timestamp}")
    return timestamp and (now - timestamp <= SPAM_RECORD_DURATION)

# clean up spam records
def cleanup_spam_records(context: CallbackContext):
    now = datetime.now(timezone.utc)
    expired_messages = []

    for message_text, timestamp in list(SPAM_RECORDS.items()):
        if now - timestamp > SPAM_RECORD_DURATION:
            expired_messages.append(message_text)
            del SPAM_RECORDS[message_text]
            print(f"[CLEANUP] Removed expired spam record: '{message_text}'")

    if not expired_messages:
        print("[CLEANUP] No expired spam messages to remove.")

def contains_non_x_links(text: str) -> bool:
    # Matches all URLs
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)

    for url in urls:
        # Allow only Twitter/X links
        if not re.search(r'https?://(www\.)?(x\.com|twitter\.com)/[^\s]+', url):
            return True  # Found a non-X link
    return False

def check_message(update: Update, context: CallbackContext):
    should_skip_spam_check = False
    
    message = update.message or update.channel_post  # Handle both messages and channel posts
    if not message:
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = update.effective_user

    print(f"==== New Message Detected ====")
    print(f"User: {user.username} (ID: {user.id})")
    print(f"Message ID: {message.message_id}")
    
    # Check for different types of content
    
    if message.photo:
        print("==== Photo Detected ====")
        print(f"Caption: {message.caption}")
        print(f"Photo sizes: {message.photo}") 

    elif message.video:
        print("==== Video Detected ====")
        print(f"Caption: {message.caption}")
        print(f"Video details: {message.video}")

    elif message.document:
        print("==== Document Detected ====")
        print(f"Document details: {message.document}")

    elif message.sticker:
        print("==== Sticker Detected ====")
        print(f"Sticker details: {message.sticker}")

    elif message.voice:
        print("==== Voice Message Detected ====")
        print(f"Voice details: {message.voice}")

    elif message.audio:
        print("==== Audio Message Detected ====")
        print(f"Audio details: {message.audio}")
        
    elif message.animation:
        print("==== Animation Detected ====")
        print(f"Animation details: {message.animation}")

    elif message.forward_from:
        print("==== Forwarded Message Detected ====")
        print(f"From: {message.forward_from.username} (ID: {message.forward_from.id})")
    
    elif message.reply_markup and message.reply_markup.inline_keyboard:
        print("==== Inline Buttons Detected ====")
        print(f"Inline keyboard: {message.reply_markup.inline_keyboard}")
    
    elif message.text:
        print("==== Text Message Detected ====")
        print(f"Text: {message.text}")

    message_text = message.text.lower()

    # Fetch chat admins to prevent acting on their messages
    chat_admins = context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in chat_admins]
    
    # If the message starts with /say, the bot will send a message on behalf of the admin
    if message_text.startswith('/say '):
        # Ensure the user is an admin (using admin_ids already fetched)
        if user_id in admin_ids:
            # Get the message after the /say command
            say_message = message_text[len('/say '):].strip()
                        
            # Ensure the message is not empty
            if say_message:
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                # Send the message as the bot
                context.bot.send_message(
                    chat_id=chat_id,
                    text=say_message,
                    parse_mode=ParseMode.HTML  # If you want to support HTML formatting
                )
            else:
                print("Empty say_message, skipping send.") 
            return  # After processing /say, exit the function
    
    # Ignore messages from admins
    if user_id not in admin_ids:

        # check if message is too short
        if len(message_text.strip()) < 2:
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return

        # Auto-ban based on suspicious name or username
        name_username = f"{user.full_name} {user.username or ''}".lower()
        if any(keyword in name_username for keyword in SUSPICIOUS_USERNAMES):
            context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            return
        
        # Delete message if it contains non-X links
        if contains_non_x_links(message.text):
            print(f"[LINK FILTER] Message from user {user_id} contains non-X links. Deleting.")
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return

        # Check for multiplication spam
        if contains_multiplication_phrase(message_text):
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        # Check for "give x sol" or "give x solana" spam
        if contains_give_sol_phrase(message_text):
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        # Block forwarded messages from non-admins
        if message.forward_date or message.forward_from or message.forward_from_chat:
            print(f"[FORWARD DETECTED] User {user_id} forwarded a message.")
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        # 1. autospam - check if its a command or matches a filter
        for trigger in FILTERS.keys():
            normalized_trigger = trigger.strip().lower()
            pattern = rf'(?<!\w)/?{re.escape(normalized_trigger)}(_\w+)?(?!\w)'
            if re.search(pattern, message_text):
                should_skip_spam_check = True
                print(f"[SPAM CHECK SKIPPED] Message '{message_text}' matched FILTER trigger: '{trigger}'")
                break

        # 2. autospam - check whitelist
        if not should_skip_spam_check:
            if message_text.strip() in WHITELIST_PHRASES:
                print(f"[SPAM CHECK SKIPPED] Message '{message_text}' matched WHITELIST.")
                should_skip_spam_check = True

        # 3. autospam - check for spam
        if not should_skip_spam_check:
            # Run spam detection only if no FILTER trigger matched
            spammer_ids = check_for_spam(message_text, user_id)

            if check_recent_spam(message_text) and user_id not in spammer_ids:
                spammer_ids.append(user_id)

            if spammer_ids:
                print(f"Muting spammers for message: '{message_text}'")
                for spammer_id in set(spammer_ids):
                    try:
                        until_date = message.date + timedelta(seconds=MUTE_DURATION)
                        permissions = ChatPermissions(can_send_messages=False)
                        context.bot.restrict_chat_member(chat_id=chat_id, user_id=spammer_id, permissions=permissions, until_date=until_date)
                        context.bot.send_message(chat_id=chat_id, text=f"User {spammer_id} has been muted for 3 days.")
                        print(f"Muted user {spammer_id} for spam message.")
                    except Exception as e:
                        print(f"Failed to mute spammer {spammer_id}: {e}")
                return
    
        # Check for banned phrases
        for phrase in BAN_PHRASES:
            # Use word boundaries to match exact words
            if re.search(r'\b' + re.escape(phrase) + r'\b', message_text):
                print(f"[BAN MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                message.reply_text(f"arc angel fallen. {user.first_name} has been banned.")
                return

        # Check for muted phrases
        for phrase in MUTE_PHRASES:
            # Use word boundaries to match exact words
            if re.search(r'\b' + re.escape(phrase) + r'\b', message_text):
                print(f"[MUTE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                until_date = message.date + timedelta(seconds=MUTE_DURATION)
                permissions = ChatPermissions(can_send_messages=False)
                context.bot.restrict_chat_member(chat_id=chat_id, user_id=user.id, permissions=permissions, until_date=until_date)
                message.reply_text(f"{user.first_name} has been muted for 3 days.")
                return

        # Check for deleted phrases
        for phrase in DELETE_PHRASES:
            # Use word boundaries to match exact words
            if re.search(r'\b' + re.escape(phrase) + r'\b', message_text):
                print(f"[DELETE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                return

    # Filter Responses (apply to all)
    for trigger, filter_data in FILTERS.items():
        normalized_trigger = trigger.strip().lower()
        # use word boundaries but allow underscores to be appended
        pattern = rf'(?<!\w)/?{re.escape(normalized_trigger)}(_\w+)?(?!\w)'
        
        if re.search(pattern, message_text):
            response_text = filter_data.get("response_text", "")
            media_file = filter_data.get("media")
            media_type = filter_data.get("type", "gif").lower()

            if media_file:
                media_path = os.path.join(MEDIA_FOLDER, media_file)
                if os.path.exists(media_path):
                    with open(media_path, 'rb') as media:
                        if media_type in ["gif", "animation"]:
                            context.bot.send_animation(chat_id=chat_id, animation=media, caption=response_text or None)
                        elif media_type == "image":
                            context.bot.send_photo(chat_id=chat_id, photo=media, caption=response_text or None)
                        elif media_type == "video":
                            context.bot.send_video(chat_id=chat_id, video=media, caption=response_text or None)
                elif response_text:
                    message.reply_text(response_text)
            elif response_text:
                message.reply_text(response_text)
            return  # Respond only once

def list_filters(update: Update, context: CallbackContext):
    # Load the latest filters
    with open(FILTERS_FILE, 'r', encoding='utf-8') as f:
        filters = json.load(f)

    # Get and sort all triggers alphabetically (removing leading slash only for sorting)
    sorted_triggers = sorted(filters.keys(), key=lambda k: k.lstrip('/').lower())

    # Re-apply slash only if the original trigger had it
    formatted_triggers = [f"`{trigger}`" for trigger in sorted_triggers]

    # Telegram messages max out at 4096 characters
    response = "*Available Filters:*\n" + "\n".join(formatted_triggers)
    if len(response) > 4000:
        for i in range(0, len(formatted_triggers), 80):  # 80 items per message chunk
            chunk = "*Available Filters:*\n" + "\n".join(formatted_triggers[i:i+80])
            update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        update.message.reply_text(response, parse_mode="Markdown")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Get the JobQueue from the dispatcher
    job_queue = updater.job_queue

    # combot alerts

    job_queue.run_daily(lambda context: post_security_message(context, 0), time=time(hour=8, minute=0))  
    job_queue.run_daily(lambda context: post_security_message(context, 1), time=time(hour=16, minute=0))
    job_queue.run_daily(post_brand_assets, time=time(hour=0, minute=0))

    # check for expiring SPAM_RECORDS
    job_queue.run_repeating(cleanup_spam_records, interval=60, first=60)

    # output filters
    dp.add_handler(CommandHandler("filters", list_filters))

    # Add text and command message handler
    dp.add_handler(MessageHandler(Filters.text | Filters.command, check_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()