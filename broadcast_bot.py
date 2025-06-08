#!/usr/bin/env python3
import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
from telegram.error import RetryAfter
from telegram.constants import ChatAction

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable required.")

# Hardcoded list of channel IDs (no need for CHANNEL_IDS env var now)
target_chats = [
    -1002325657963,
    -1002459318891,
    -1002377542328,
    -1002375700922,
    -1002356727250,
    -1002270458781,
    -1002332733621,
    -1002322290432,
    # duplicate removed once
    -1002316584285,
    # duplicate removed once
    -1002313854344,
    # duplicate removed once
    -1002298191534,
    -1002405499416,
    -1002334756434,
    -1002326105229,
    -1002470097811,
    -1002400508273
]

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
        await update.message.reply_text("📢 How many times should I send this message? (1-100)")

    elif user_state[user_id]["step"] == "waiting_for_count":
        try:
            count = int(msg)
            if not (1 <= count <= 100):
                raise ValueError()
        except ValueError:
            await update.message.reply_text("❗ Please enter a valid number between 1 and 100.")
            return

        text = user_state[user_id]["message"]
        await update.message.reply_text(f"⏳ Sending message {count} times to all channels...\nThis will take approximately {count * 3} seconds (plus any wait if rate-limited).")

        success_counts = {chat_id: 0 for chat_id in target_chats}

        for i in range(1, count + 1):
            for chat_id in target_chats:
                while True:
                    try:
                        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                        await context.bot.send_message(chat_id=chat_id, text=text)
                        success_counts[chat_id] += 1
                        break
                    except RetryAfter as e:
                        wait = e.retry_after + 1
                        print(f"Flood limit hit for chat {chat_id}. Sleeping for {wait} seconds.")
                        await asyncio.sleep(wait)
                    except Exception as e:
                        print(f"Error sending to {chat_id}: {e}")
                        break

            await asyncio.sleep(3)  # 3 seconds delay per batch of messages to all channels

            if i % 10 == 0 or i == count:
                total_sent = sum(success_counts.values())
                msg_text = f"✅ Broadcast progress:\nSent {i} out of {count} messages.\nTotal messages sent to all channels: {total_sent}."
                try:
                    await context.bot.send_message(chat_id=user_id, text=msg_text)
                except Exception as e:
                    print(f"Failed to send progress message to user {user_id}: {e}")

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
