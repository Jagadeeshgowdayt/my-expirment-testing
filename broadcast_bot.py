import os
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHATS = os.getenv("TARGET_CHATS", "")

try:
    CHAT_IDS = [int(cid) for cid in re.findall(r"-?\d+", TARGET_CHATS)]
    if not CHAT_IDS:
        raise ValueError("No valid chat IDs found.")
except Exception as e:
    raise RuntimeError(f"Error parsing TARGET_CHATS: {e}")

# Command handler for /broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    failed = []

    for chat_id in CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")
            failed.append(str(chat_id))

    if failed:
        await update.message.reply_text(f"Sent with some errors. Failed: {', '.join(failed)}")
    else:
        await update.message.reply_text("Message sent to all target chats.")

# Entry point
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    logger.info("Bot starting...")
    app.run_polling()  # No asyncio.run() used here
