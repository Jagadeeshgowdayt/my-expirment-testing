import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import Conflict

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# In-memory store for channels
channels = set()

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your broadcast bot. Add me to channels and send me a message to broadcast.")

# Handler for all messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # If message from a channel
    if update.effective_chat.type == "channel":
        channels.add(update.effective_chat.id)
        logging.info(f"Added channel: {update.effective_chat.title} ({update.effective_chat.id})")

    # Broadcast the message to all known channels
    for channel_id in channels:
        try:
            await context.bot.copy_message(
                chat_id=channel_id,
                from_chat_id=message.chat_id,
                message_id=message.message_id
            )
        except Exception as e:
            logging.error(f"Failed to send to channel {channel_id}: {e}")

# Global error handler to suppress getUpdates Conflict error
def global_error_handler(update, context):
    if isinstance(context.error, Conflict):
        logging.warning("Conflict error suppressed: another polling instance is likely running.")
        return
    logging.error("Error while handling update", exc_info=context.error)

# Run the bot
def main():
    TOKEN = "YOUR_BOT_TOKEN"

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Global error handler
    app.add_error_handler(global_error_handler)

    # Start polling
    logging.info("Bot started with polling")
    app.run_polling()

if __name__ == '__main__':
    main()
