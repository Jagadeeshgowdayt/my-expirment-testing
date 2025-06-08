#!/usr/bin/env python3
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, ChatMemberUpdated, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_FILE = "channels.json"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable required.")

# Load or init channel list
if os.path.exists(CHANNEL_FILE):
    with open(CHANNEL_FILE, "r") as f:
        target_chats = json.load(f)
else:
    target_chats = []

# Health-check server
def run_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    HTTPServer(("0.0.0.0", 8443), HealthHandler).serve_forever()

# When bot is made admin in a channel, record it
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cm: ChatMemberUpdated = update.chat_member
    old, new = cm.old_chat_member, cm.new_chat_member
    if new.user.id == context.bot.id and new.status == ChatMember.ADMINISTRATOR:
        chat_id = cm.chat.id
        if chat_id not in target_chats:
            target_chats.append(chat_id)
            with open(CHANNEL_FILE, "w") as f:
                json.dump(target_chats, f)

# Broadcast every text message to all recorded channels
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    for chat_id in target_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")
    # Optionally confirm to sender:
    await update.message.reply_text("✅ Broadcast sent to all channels.")

def main():
    # Start health-check server
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server on 8443")

    # Build and register handlers
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast))

    print("Bot starting…")
    app.run_polling()

if __name__ == "__main__":
    main()
    
