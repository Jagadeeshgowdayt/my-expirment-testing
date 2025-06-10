import os
import asyncio
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Read from environment
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_IDS = os.environ["CHANNEL_IDS"]

# Parse comma-separated channel IDs
CHANNEL_IDS = [int(cid.strip()) for cid in CHANNEL_IDS.split(",") if cid.strip()]
user_message = None  # Store message globally


# Health check server to satisfy Koyeb
async def health_check(request):
    return web.Response(text="OK")

async def run_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8443)
    await site.start()


# Bot logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send the message you'd like to broadcast to all channels.")

async def capture_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_message
    user_message = update.message.text
    await update.message.reply_text(
        f"📝 Message saved:\n\n{user_message}\n\nSend /confirm to broadcast this message 100 times."
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_message
    if not user_message:
        await update.message.reply_text("❌ No message set yet. Please send a message first.")
        return

    await update.message.reply_text("🚀 Sending message to channels 100 times...")

    bot: Bot = context.bot
    for i in range(100):
        for chat_id in CHANNEL_IDS:
            try:
                await bot.send_message(chat_id=chat_id, text=user_message)
            except Exception as e:
                print(f"Error sending to {chat_id}: {e}")

    await update.message.reply_text("✅ Message broadcast completed.")


# Start everything
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_message))

    await asyncio.gather(
        app.initialize(),
        run_health_server(),
        app.start(),
        app.updater.start_polling()
    )

if __name__ == "__main__":
    asyncio.run(main())
