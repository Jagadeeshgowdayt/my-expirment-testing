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
CHANNEL_IDS = os.getenv("CHANNEL_IDS", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable required.")

try:
    target_chats = [int(cid.strip()) for cid in CHANNEL_IDS.split(",") if cid.strip()]
except ValueError:
    raise RuntimeError("CHANNEL_IDS must be comma-separated integers.")

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
        await update.message.reply_text(f"⏳ Sending message {count} times to all channels...\nThis will take approximately {count} minutes.")

        # Track how many messages successfully sent per channel
        success_counts = {chat_id: 0 for chat_id in target_chats}

        # Send messages with ~60 seconds delay per message per channel
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

            # After sending message i to all channels, wait ~60 seconds before next batch
            await asyncio.sleep(60)

            # Every 10 messages sent, notify user of progress
            if i % 10 == 0 or i == count:
                # Prepare progress message
                total_sent = sum(success_counts.values())
                msg_text = f"✅ Broadcast progress:\nSent {i} out of {count} messages.\n" \
                           f"Total messages sent to all channels: {total_sent}."
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
    
