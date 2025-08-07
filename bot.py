import os
import json
import random
import string
import threading
import asyncio
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes
)

# 🔐 Replace this with your real Telegram user ID
ADMIN_ID = 123456789  # <-- CHANGE THIS
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # <-- CHANGE THIS

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is live"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Aizen Bot ✨\nUse This Command /redeem"
    )

# 🎟️ /redeem
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    if not args:
        await update.message.reply_text("❌ Please use like /redeem your_message_here")
        return

    await update.message.reply_text("Processing 🗝️")
    user = update.effective_user
    text = f"📩 New Redeem Request:\nFrom: {user.full_name} (@{user.username})\nUserID: {user.id}\n\nMessage:\n{args}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)

# 📥 /reply
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /reply user_id your_message")
        return

    user_id = int(context.args[0])
    msg = " ".join(context.args[1:])
    await context.bot.send_message(chat_id=user_id, text=msg)
    await update.message.reply_text("✅ Message sent.")

# 📢 /broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("❌ Usage: /broadcast your_message")
        return

    if os.path.exists("premium_users.json"):
        with open("premium_users.json", "r") as f:
            users = json.load(f)
        for uid in users:
            try:
                await context.bot.send_message(chat_id=int(uid), text=message)
            except:
                pass

    await update.message.reply_text("✅ Broadcast sent.")

# 🔑 /genk
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def genk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage: /genk <days>")
        return

    days = int(context.args[0])
    key = generate_key()
    expiry = (datetime.utcnow() + timedelta(days=days)).isoformat()

    keys = {}
    if os.path.exists("keys.json"):
        with open("keys.json", "r") as f:
            keys = json.load(f)

    keys[key] = expiry

    with open("keys.json", "w") as f:
        json.dump(keys, f)

    await update.message.reply_text(f"🗝️ Generated Key: `{key}` (Valid {days} days)", parse_mode="Markdown")

# 🧑‍💻 /premium
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please enter a key like: /premium YOUR_KEY")
        return

    input_key = context.args[0].strip().upper()
    user = update.effective_user

    if not os.path.exists("keys.json"):
        await update.message.reply_text("❌ Invalid Key")
        return

    with open("keys.json", "r") as f:
        keys = json.load(f)

    if input_key not in keys:
        await update.message.reply_text("❌ Invalid Key")
        return

    expiry = keys[input_key]
    del keys[input_key]
    with open("keys.json", "w") as f:
        json.dump(keys, f)

    users = {}
    if os.path.exists("premium_users.json"):
        with open("premium_users.json", "r") as f:
            users = json.load(f)

    users[str(user.id)] = expiry
    with open("premium_users.json", "w") as f:
        json.dump(users, f)

    await update.message.reply_text("✅ Access Granted. Welcome to Premium 🔥")

    msg = (
        f"🔐 New Premium Activation:\n"
        f"User: {user.full_name} (@{user.username})\n"
        f"UserID: {user.id}\n"
        f"Valid Until: {expiry}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

# ⏰ Auto check expiry every 24h
async def check_premium_expiry(bot: Bot):
    while True:
        users = {}
        if os.path.exists("premium_users.json"):
            with open("premium_users.json", "r") as f:
                users = json.load(f)

        updated_users = {}
        now = datetime.utcnow()

        for uid, exp in users.items():
            if datetime.fromisoformat(exp) <= now:
                try:
                    await bot.send_message(chat_id=int(uid), text="👋 Your premium has ended.")
                except:
                    pass
            else:
                updated_users[uid] = exp

        with open("premium_users.json", "w") as f:
            json.dump(updated_users, f)

        await asyncio.sleep(86400)  # 24h

# 🚀 Main
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("reply", reply))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("genk", genk))
    app.add_handler(CommandHandler("premium", premium))

    # 🔄 Expiry checker
    bot_instance = Bot(BOT_TOKEN)
    app.job_queue.run_once(lambda *_: asyncio.create_task(check_premium_expiry(bot_instance)), 1)

    app.run_polling()
