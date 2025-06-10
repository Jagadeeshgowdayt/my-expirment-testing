import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health check server for Koyeb
def run_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
    HTTPServer(("0.0.0.0", 8443), HealthHandler).serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
TARGET_CHATS = os.getenv("TARGET_CHATS", "")

# Parse target chat IDs
try:
    CHAT_IDS = [int(chat_id.strip()) for chat_id in TARGET_CHATS.split(",") if chat_id.strip()]
except ValueError as e:
    raise RuntimeError(f"Error parsing TARGET_CHATS: {e}")

# State tracking
message_to_send = {}
confirmed = {}

# Authorization check
def is_authorized(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def unauthorized(update: Update):
    await update.message.reply_text("❌ You are not authorized.")

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return await unauthorized(update)
    await update.message.reply_text("Send the message you'd like to broadcast to all channels.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return await unauthorized(update)

    text = update.message.text.strip()
    if user_id not in message_to_send:
        message_to_send[user_id] = text
        confirmed[user_id] = False
        await update.message.reply_text(
            f"🔔 Confirm to send this message 100 times to all channels:\n\n{text}\n\n"
            "Reply with /confirm to continue or /cancel to abort."
        )
    else:
        await update.message.reply_text("You've already set a message. Use /cancel to reset.")

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return await unauthorized(update)

    if user_id in message_to_send and not confirmed.get(user_id):
        confirmed[user_id] = True
        await update.message.reply_text("✅ Confirmed. Sending messages...")
        for _ in range(100):
            for chat_id in CHAT_IDS:
                try:
                    await context.bot.send_message(chat_id=chat_id, text=message_to_send[user_id])
                except Exception as e:
                    logger.error(f"Failed to send to {chat_id}: {e}")
        await update.message.reply_text("📨 Done broadcasting!")
        message_to_send.pop(user_id)
        confirmed.pop(user_id)
    else:
        await update.message.reply_text("❌ No message to confirm or already confirmed.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return await unauthorized(update)

    message_to_send.pop(user_id, None)
    confirmed.pop(user_id, None)
    await update.message.reply_text("🛑 Canceled. You can now send a new message.")

# Main function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
