import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = os.getenv("CHANNEL_IDS", "")
CONFIRM_USER_ID = int(os.getenv("CONFIRM_USER_ID", "0"))

if not BOT_TOKEN or not CHANNEL_IDS or CONFIRM_USER_ID == 0:
    raise RuntimeError("BOT_TOKEN, CHANNEL_IDS, and CONFIRM_USER_ID must be set.")

CHANNEL_IDS = [int(cid.strip()) for cid in CHANNEL_IDS.split(",") if cid.strip()]
custom_messages = {}  # Store message per user

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CONFIRM_USER_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return

    await update.message.reply_text(
        "👋 Send me the message you want to broadcast (just type it)."
    )

# Receive custom message
async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CONFIRM_USER_ID:
        return

    msg = update.message.text.strip()
    if not msg:
        await update.message.reply_text("❌ Message is empty.")
        return

    custom_messages[update.effective_user.id] = msg

    # Ask confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data="confirm_send"),
            InlineKeyboardButton("❌ No", callback_data="cancel_send")
        ]
    ]
    await update.message.reply_text(
        f"📝 Message to send *100 times* to *{len(CHANNEL_IDS)} channels*:\n\n{msg}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Handle button press
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if user_id != CONFIRM_USER_ID:
        await query.edit_message_text("❌ You are not authorized.")
        return

    if query.data == "confirm_send":
        message = custom_messages.get(user_id)
        if not message:
            await query.edit_message_text("⚠️ No message found. Please send it again.")
            return

        await query.edit_message_text("🚀 Sending messages...")

        sent_count = 0
        for i in range(100):
            for channel_id in CHANNEL_IDS:
                try:
                    await context.bot.send_message(chat_id=channel_id, text=message)
                    sent_count += 1
                except Exception as e:
                    print(f"Failed to send to {channel_id}: {e}")

        await context.bot.send_message(chat_id=user_id, text=f"✅ Done! Sent {sent_count} messages.")
    elif query.data == "cancel_send":
        await query.edit_message_text("❌ Cancelled.")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), save_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot started.")
    app.run_polling()
