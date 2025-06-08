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
    ConversationHandler,
    CommandHandler,
)
from telegram.constants import ChatAction

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = os.getenv("CHANNEL_IDS", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable required.")

try:
    target_chats = [int(cid.strip()) for cid in CHANNEL_IDS.split(",") if cid.strip()]
except ValueError:
    raise RuntimeError("CHANNEL_IDS must be comma-separated integers.")

# For tracking message and step
user_state = {}

def run_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    server = HTTPServer(("0.0.0.0", 8443), HealthHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me the message you want to broadcast.")
    user_state[update.effective_user.id] = {"step": "waiting_for_message"}
    
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text

    if user_id not in user_state:
        await update.message.reply_text("Send /start to begin a broadcast.")
        return

    if user_state[user_id]["step"] == "waiting_for_message":
        user_state[user_id]["message"] = msg
        user_state[user_id]["step"] = "waiting_for_count"
        await update.message.reply_text("📢 How many times should I send this message?")
    
    elif user_state[user_id]["step"] == "waiting_for_count":
        try:
            count = int(msg)
            if not (1 <= count <= 100):
                raise ValueError()
        except ValueError:
            await update.message.reply_text("❗ Please enter a valid number between 1 and 100.")
            return
        
        text = user_state[user_id]["message"]
        await update.message.reply_text(f"⏳ Sending message {count} times to all channels...")

        for i in range(count):
            for chat_id in target_chats:
                try:
                    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                    await context.bot.send_message(chat_id=chat_id, text=text)
                except Exception as e:
                    print(f"Error sending to {chat_id}: {e}")

        await update.message.reply_text("✅ Broadcast complete.")
        del user_state[user_id]

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Please use /start to begin.")

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server listening on port 8443")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Bot is starting…")
    app.run_polling()

if __name__ == "__main__":
    main()
    
