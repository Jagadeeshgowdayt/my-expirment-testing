#!/usr/bin/env python3
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, ChatMemberUpdated, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)

# --- Load configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # your Telegram user ID
CHANNEL_FILE = "channels.json"

if not BOT_TOKEN or not OWNER_ID:
    raise RuntimeError("Both BOT_TOKEN and OWNER_ID environment variables must be set.")

# Persisted list of channel IDs
if os.path.exists(CHANNEL_FILE):
    with open(CHANNEL_FILE, "r") as f:
        target_chats = json.load(f)
else:
    target_chats = []

# --- Health-check HTTP server ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    HTTPServer(("0.0.0.0", 8443), HealthHandler).serve_forever()

# --- Telegram Handlers ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only the owner can broadcast, via private chat
    if update.effective_chat.type != "private" or update.effective_user.id != OWNER_ID:
        return
    text = update.message.text
    for chat_id in target_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
    await update.message.reply_text("✅ Broadcast sent to all channels.")

async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cm: ChatMemberUpdated = update.chat_member
    old, new = cm.old_chat_member, cm.new_chat_member
    # If bot itself was promoted to ADMIN in a channel
    if new.user.id == context.bot.id and new.status == ChatMember.ADMINISTRATOR:
        chat = cm.chat
        chat_id = chat.id
        if chat_id not in target_chats:
            # Prompt owner to confirm addition
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=(
                    f"Bot added as admin in channel '{chat.title}' (ID: {chat_id}).\n"
                    f"Reply with `/addchannel {chat_id}` to include it in broadcasts."
                ),
            )

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only owner via private chat
    if update.effective_chat.type != "private" or update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args:
        return await update.message.reply_text("Usage: /addchannel <channel_id>")
    try:
        chat_id = int(args[0])
    except ValueError:
        return await update.message.reply_text("❌ Invalid channel ID; must be a number.")
    if chat_id in target_chats:
        return await update.message.reply_text("⚠️ Channel already in broadcast list.")
    target_chats.append(chat_id)
    with open(CHANNEL_FILE, "w") as f:
        json.dump(target_chats, f)
    await update.message.reply_text(f"✅ Channel {chat_id} added to broadcast list.")

def main():
    # Start health-check server
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server listening on 8443")

    # Build bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # Register handlers
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, broadcast))
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("addchannel", add_channel_command))
    print("Bot is starting…")
    app.run_polling()

if __name__ == "__main__":
    main()
    
