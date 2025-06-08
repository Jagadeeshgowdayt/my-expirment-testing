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

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # your user ID
CHANNEL_FILE = "channels.json"

if not BOT_TOKEN or OWNER_ID == 0:
    raise RuntimeError("Set BOT_TOKEN and OWNER_ID environment vars.")

# Load or initialize channel list
if os.path.exists(CHANNEL_FILE):
    with open(CHANNEL_FILE, "r") as f:
        target_chats = json.load(f)
else:
    target_chats = []

# Health-check HTTP server on port 8443
def run_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    HTTPServer(("0.0.0.0", 8443), HealthHandler).serve_forever()

# Broadcast private messages from owner to all channels
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = update.message.text
    for chat_id in target_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")
    await update.message.reply_text("✅ Broadcast sent.")

# Detect when bot is added as admin
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cm: ChatMemberUpdated = update.chat_member
    old, new = cm.old_chat_member, cm.new_chat_member
    if new.user.id == context.bot.id and new.status == ChatMember.ADMINISTRATOR:
        chat = cm.chat
        chat_id = chat.id
        title = chat.title or chat_id
        if chat_id not in target_chats:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=(
                    f"Bot added as admin in channel '{title}' (ID: {chat_id}).\n"
                    f"Use /addchannel {chat_id} to include it in broadcasts."
                ),
            )

# Owner confirms adding the channel
async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        return await update.message.reply_text("Usage: /addchannel <channel_id>")
    try:
        chat_id = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("Invalid ID.")
    if chat_id in target_chats:
        return await update.message.reply_text("Channel already added.")
    target_chats.append(chat_id)
    with open(CHANNEL_FILE, "w") as f:
        json.dump(target_chats, f)
    await update.message.reply_text(f"Channel {chat_id} added.")

# Main entry point
def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server on port 8443")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, broadcast))
    app.add_handler(CommandHandler("addchannel", add_channel_command))

    print("Bot starting…")
    app.run_polling()

if __name__ == "__main__":
    main()
    
