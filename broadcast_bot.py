#!/usr/bin/env python3
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, ChatMemberUpdated
from telegram.ext import ApplicationBuilder, MessageHandler, ChatMemberHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_FILE = "channels.json"

# Load channel list
if os.path.exists(CHANNEL_FILE):
    with open(CHANNEL_FILE, "r") as f:
        channels = json.load(f)
else:
    channels = []

def run_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
    HTTPServer(("0.0.0.0", 8443), HealthHandler).serve_forever()

# When bot is added to channel as admin
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member_update = update.chat_member
    new = member_update.new_chat_member
    if new.user.id == context.bot.id and new.status == "administrator":
        chat_id = member_update.chat.id
        if chat_id not in channels:
            channels.append(chat_id)
            with open(CHANNEL_FILE, "w") as f:
                json.dump(channels, f)
            print(f"✅ Added channel {chat_id}")

# Broadcast handler
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    for chat_id in channels:
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg)
        except Exception as e:
            print(f"❌ Failed to send to {chat_id}: {e}")
    await update.message.reply_text("✅ Sent to all channels.")

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatMemberHandler(handle_admin, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast))
    app.run_polling()

if __name__ == "__main__":
    main()
    
