import logging
import os
import ast
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Load bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set.")

# Load and parse channel IDs
raw_chat_ids = os.getenv("TARGET_CHATS")
if not raw_chat_ids:
    raise RuntimeError("TARGET_CHATS environment variable is missing.")

try:
    target_chats = ast.literal_eval(raw_chat_ids)
    if not isinstance(target_chats, list) or not all(isinstance(x, int) for x in target_chats):
        raise ValueError("TARGET_CHATS must be a list of integers.")
except Exception as e:
    raise RuntimeError(f"Error parsing TARGET_CHATS: {e}")


# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Hello! Send me a message and I’ll forward it to all connected channels.")


# Message handler: forward text to all channels
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if not text:
        return

    count = 0
    for chat_id in target_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
        except Exception as e:
            logger.error(f"❌ Failed to send message to {chat_id}: {e}")

    await update.message.reply_text(f"✅ Broadcast sent to {count} channel(s).")


# Main function to start the bot
async def main():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .drop_pending_updates(True)  # Prevents getUpdates conflict
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), forward_message))

    print("🤖 Bot started and polling...")
    await application.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
