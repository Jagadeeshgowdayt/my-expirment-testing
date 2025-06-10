import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHATS = os.environ.get("TARGET_CHATS")

# Parse chat IDs as integers
try:
    CHAT_IDS = [int(chat_id.strip()) for chat_id in TARGET_CHATS.split(",") if chat_id.strip()]
except Exception as e:
    raise RuntimeError(f"Error parsing TARGET_CHATS: {e}")

# Broadcast function
async def broadcast(message: str, context: ContextTypes.DEFAULT_TYPE):
    for chat_id in CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            logging.info(f"Sent message to {chat_id}")
        except Exception as e:
            logging.error(f"Failed to send to {chat_id}: {e}")

# /broadcast command handler
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast your message here")
        return
    msg = " ".join(context.args)
    await broadcast(msg, context)
    await update.message.reply_text("Broadcast sent!")

# Main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("broadcast", broadcast_command))

    logging.info("Bot started.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
