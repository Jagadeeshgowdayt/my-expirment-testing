import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Your bot token from BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# List of channel usernames or chat IDs (must include @ if using usernames)
CHANNELS = [
    "@channel_username1",
    "@channel_username2",
    "-1001234567890",  # Example of a private channel ID
]

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Message handler to broadcast any received message
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    msg = update.message.text
    success = 0
    fail = 0

    for channel in CHANNELS:
        try:
            await context.bot.send_message(chat_id=channel, text=msg)
            success += 1
        except Exception as e:
            logger.warning(f"Failed to send to {channel}: {e}")
            fail += 1

    await update.message.reply_text(f"✅ Sent to {success} channel(s), ❌ Failed: {fail}")

# Main entry point
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_handler))

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
