#!/usr/bin/env python3
import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
from telegram.error import RetryAfter
from telegram.constants import ChatAction

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN must be set in env")

# --- FULL LIST OF 150+ CHANNEL IDs ---
target_chats = [
    -1002325657963,-1002459318891,-1002377542328,-1002375700922,-1002356727250,
    -1002270458781,-1002332733621,-1002322290432,-1002316584285,-1002313854344,
    -1002298191534,-1002405499416,-1002334756434,-1002326105229,-1002470097811,
    -1002400508273,-1001915538385,-1001879820897,-1001736885498,-1001880130215,
    -1001866122329,-1001829940759,-1001853238197,-1001839670663,-1001790524856,
    -1002440329413,-1002391297123,-1002479066479,-1002447041438,-1002428531554,
    -1002396633921,-1002393972379,-1002391581446,-1002416438621,-1002389156597,
    -1002381054313,-1002355738386,-1002354139577,-1002325494721,-1002264136374,
    -1002454109043,-1002361031846,-1002297621021,-1002387635064,-1002369154856,
    -1002343378994,-1002165407370,-1002381673517,-1002320553959,-1002316952736,
    -1002185777109,-1002185456336,-1002444469909,-1002420439739,-1002418304148,
    -1002396947792,-1002387969728,-1001587576820,-1001866854321,-1001863477657,
    -1001831136673,-1001565287646,-1001501250440,-1001968785691,-1001835227113,
    -1001813178855,-1001970632176,-1001890509321,-1001962158303,-1002480781332,
    -1002472866446,-1002427044876,-1002418660666,-1002265521671,-1002297685575,
    -1002264257777,-1002435288047,-1002421204046,-1002397419696,-1002302168426,
    -1002495730326,-1002351025864,-1002349671984,-1002337503460,-1002306232513,
    -1002303298531,-1002496525301,-1002476968637,-1002381237917,-1002375839378,
    -1002198979040,-1002491206428,-1002447801891,-1002355257067,-1002350509360,
    -1002275974805,-1002386051396,-1002380073568,-1002329647297,-1002275787537,
    -1002354141641,-1002483226993,-1002380322431,-1002257023517,-1002334743419,
    -1002346699889,-1002360903201,-1002325885059,-1002388220538,-1002395148579,
    -1002332369590,-1002414481740,-1002366013887,-1002395748367,-1002459708952,
    -1002480694569,-1002262948735,-1002397410561,-1002378275214,-1002383624274,
    -1002340719164,-1002456800807,-1002472748043,-1002478674999,-1002338481405,
    -1002315556175,-1002303341016,-1002458319949,-1002376359174,-1002295539465,
    -1002290615630,-1002289626071,-1002473823843,-1002345208320,-1002326838843,
    -1002298728314,-1002478774581,-1002455993815,-1002236896519,-1002480463250,
    -1002434122122,-1002394105705,-1002286577506,-1002279344352,-1002256115337,
    -1002479474066,-1002453842994
]

# --- HEALTH CHECK SERVER (port 8443) ---
def run_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
    HTTPServer(("0.0.0.0", 8443), HealthHandler).serve_forever()

# --- BROADCAST FLOW ---
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me the message you want to broadcast.")
    user_state[update.effective_user.id] = {"step": "awaiting_message"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if uid not in user_state:
        return await update.message.reply_text("Send /start to begin.")

    state = user_state[uid]
    # Step 1: receive the message to broadcast
    if state["step"] == "awaiting_message":
        state["message"] = text
        state["step"] = "awaiting_count"
        return await update.message.reply_text("📢 How many times? (1-100)")

    # Step 2: receive count and perform broadcast
    count = 0
    if state["step"] == "awaiting_count":
        try:
            count = int(text)
            if not 1 <= count <= 100:
                raise ValueError()
        except:
            return await update.message.reply_text("❗ Enter a number between 1 and 100.")
        state["step"] = "broadcasting"
        await update.message.reply_text(
            f"⏳ Broadcasting {count}× to {len(target_chats)} channels...\n"
            f"▷ ~3s delay/batch, progress every 10 sends."
        )

        success = 0
        for i in range(1, count + 1):
            for cid in target_chats:
                try:
                    # typing indicator
                    await context.bot.send_chat_action(cid, action=ChatAction.TYPING)
                    await context.bot.send_message(cid, state["message"])
                    success += 1
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after + 1)
                    continue
                except:
                    continue
            # delay between each batch
            await asyncio.sleep(3)
            # progress update every 10 messages
            if i % 10 == 0 or i == count:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"✅ Progress: sent {i}/{count} rounds ({success} total messages)."
                )

        await update.message.reply_text(f"✅ Done! Total messages sent: {success}")
        del user_state[uid]

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Use /start to begin broadcasting.")

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server on port 8443")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
