import os
import asyncio
import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)
from fastapi import FastAPI

# Read environment variables
TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHATS = os.getenv("TARGET_CHATS", "")
CHAT_IDS = [int(chat_id.strip()) for chat_id in TARGET_CHATS.split(",") if chat_id.strip()]

# FastAPI app for health check
app_fastapi = FastAPI()

@app_fastapi.get("/")
def root():
    return {"status": "ok"}

def start_fastapi():
    import uvicorn
    uvicorn.run(app_fastapi, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Global variable to store custom message
custom_message = None

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /set <your message> to set the message. Then use /send to broadcast.")

# /set command to set a message
async def set_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global custom_message
    custom_message = " ".join(context.args)
    if custom_message:
        await update.message.reply_text(f"✅ Message set:\n\n{custom_message}")
    else:
        await update.message.reply_text("⚠️ Please provide a message after /set")

# /send command to confirm and broadcast
async def send_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global custom_message
    if not custom_message:
        await update.message.reply_text("⚠️ No message set yet. Use /set <your message> first.")
        return

    await update.message.reply_text("✅ Broadcasting will start now...")

    for i in range(100):
        for chat_id in CHAT_IDS:
            try:
                await context.bot.send_message(chat_id=chat_id, text=custom_message)
                await asyncio.sleep(0.1)  # throttle to avoid rate limits
            except Exception as e:
                print(f"❌ Error sending to {chat_id}: {e}")

    await update.message.reply_text("✅ Message sent 100 times to all channels.")

# Main function
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_msg))
    app.add_handler(CommandHandler("send", send_msg))

    # Start FastAPI health check server
    threading.Thread(target=start_fastapi, daemon=True).start()

    print("🚀 Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
