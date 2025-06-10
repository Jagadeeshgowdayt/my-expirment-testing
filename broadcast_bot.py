import os
from telegram import Bot

# --- CONFIGURATION ---

BOT_TOKEN = os.getenv("BOT_TOKEN")  # from environment variable
CHANNEL_IDS = os.getenv("CHANNEL_IDS", "").split(",")  # comma-separated list
MESSAGE = os.getenv("MESSAGE", "Hello from my bot!")  # default message

# --- SCRIPT STARTS HERE ---

bot = Bot(token=BOT_TOKEN)

# Convert channel IDs to int safely
channel_ids = [int(chat_id.strip()) for chat_id in CHANNEL_IDS if chat_id.strip()]

for i, chat_id in enumerate(channel_ids, 1):
    try:
        bot.send_message(chat_id=chat_id, text=MESSAGE)
        print(f"[{i}] Sent to {chat_id}")
    except Exception as e:
        print(f"[{i}] Failed to send to {chat_id}: {e}")
