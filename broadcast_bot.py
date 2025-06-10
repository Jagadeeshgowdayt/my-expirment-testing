import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

# ✅ Replace this with your real bot token from BotFather
BOT_TOKEN = "1234567890:ABCDefghIJKlmNOPqrsTUVwxyZ-1234567890"

# Store all chat IDs the bot is added to
chat_ids = set()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ✅ When bot receives any message in a group/channel, store chat ID
async def register_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in chat_ids:
        chat_ids.add(chat_id)
        logger.info(f"Registered new chat: {chat_id}")
    return


# ✅ When you send a message privately to the bot, it will broadcast it to all known chats
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return  # Only allow broadcasting from private chat

    text = update.message.text
    failures = 0

    for cid in chat_ids:
        try:
            await context.bot.send_message(chat_id=cid, text=text)
        except Exception as e:
            logger.warning(f"Failed to send to {cid}: {e}")
            failures += 1

    await update.message.reply_text(
        f"Broadcast complete. Sent to {len(chat_ids) - failures} chats."
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Listen to any message in group/channel to track chats
    app.add_handler(MessageHandler(filters.ALL & (~filters.ChatType.PRIVATE), register_chat))

    # Listen to private messages for broadcasting
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, broadcast_message))

    logger.info("Bot started with polling")
    app.run_polling()


if __name__ == "__main__":
    main()
