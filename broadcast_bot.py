#!/usr/bin/env python3
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)

# Load configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = os.getenv("CHANNEL_IDS")  # comma-separated list of chat IDs

if not BOT_TOKEN or not CHANNEL_IDS:
    raise RuntimeError("Both BOT_TOKEN and CHANNEL_IDS environment variables must be set.")

# Parse target channel IDs into integers
target_chats = [int(cid.strip()) for cid in CHANNEL_IDS.split(",") if cid.strip()]

# ---------------- Health Check Server ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


def run_health_server():
    HTTPServer(("0.0.0.0", 8443), HealthHandler).serve_forever()

# ---------------- Telegram Handlers ----------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only accept messages in private chat
    if update.effective_chat.type != "private":
        return
    text = update.message.text
    for chat_id in target_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
    # Confirm completion to the sender
    await update.message.reply_text("✅ Broadcast sent to all channels.")


def main():
    # Start HTTP health server in background
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server listening on port 8443")

    # Build and run the Telegram bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, broadcast))
    print("Bot is starting…")
    app.run_polling()


if __name__ == "__main__":
    main()
