
    cm: ChatMemberUpdated = update.chat_member
    old, new = cm.old_chat_member, cm.new_chat_member
    # Check if this update is for the bot's status in the chat
    if new.user.id == context.bot.id and new.status == ChatMember.ADMINISTRATOR:
        chat = cm.chat
        chat_id = chat.id
        if chat_id not in target_chats:
            # Prompt owner to confirm adding this channel
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"Bot added as admin in channel '{chat.title}' (ID: {chat_id}).\n" +
                     "Reply with /addchannel {chat_id} to include it in broadcasts."
            )

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Owner confirms adding channel
    if update.effective_chat.type != "private" or update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /addchannel <channel_id>")
        return
    try:
        chat_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid channel ID. It must be an integer.")
        return
    if chat_id in target_chats:
        await update.message.reply_text(f"Channel {chat_id} is already in the broadcast list.")
        return
    target_chats.append(chat_id)
    # Persist to file
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(target_chats, f)
    await update.message.reply_text(f"Channel {chat_id} added to broadcast list.")


def main():
    # Start HTTP health server in background
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server listening on port 8443")

    # Build and run the Telegram bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # Handlers
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, broadcast))
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("addchannel", add_channel_command))
    print("Bot is starting…")
    app.run_polling()

if __name__ == "__main__":
    main()
