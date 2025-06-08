#!/usr/bin/env python3
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = os.getenv("CHANNEL_IDS", "")  # comma-separated list of channel IDs

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable required.")

# Parse CHANNEL_IDS into a list of integers
try:
    target_chats = [int(cid.strip()) for cid in CHANNEL_IDS.split(",") if cid.strip()]
except ValueError:
    raise RuntimeError("CHANNEL_IDS must be comma-separated integers.")

# Health-check HTTP server on port 8443
def run_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    server = HTTPServer(("0.0.0.0", 8443), HealthHandler)
    server.serve_forever()

# Broadcast handler
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    for chat_id in target_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")
    await update.message.reply_text("✅ Broadcast sent.")

# Start bot and HTTP health check
def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server listening on port 8443")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast))
    
    print("Bot is starting…")
    app.run_polling()

if __name__ == "__main__":
    main()
