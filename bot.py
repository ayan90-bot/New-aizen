import os
import json
import random
import string
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === FILE PATHS ===
KEY_FILE = "keys.json"
PREMIUM_FILE = "premium_users.json"

# === FLASK SERVER ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

# === UTILS ===
def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def generate_key(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Aizen Bot ✨\nUse this command /redeem")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter key 🗝️")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()
    keys = load_json(KEY_FILE)
    users = load_json(PREMIUM_FILE)

    if text in keys:
        days = keys[text]
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        users[user_id] = expiry_date
        save_json(PREMIUM_FILE, users)

        del keys[text]
        save_json(KEY_FILE, keys)

        await update.message.reply_text(f"✅ Premium Activated Till: {expiry_date}")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 User {user_id} redeemed a key for {days} days.\nExpiry: {expiry_date}"
        )
    else:
        await update.message.reply_text("❌ Invalid Key.")

async def genk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        days = int(context.args[0])
    except:
        await update.message.reply_text("❌ Usage: /genk <days>")
        return

    key = generate_key()
    keys = load_json(KEY_FILE)
    keys[key] = days
    save_json(KEY_FILE, keys)

    await update.message.reply_text(
        f"✅ Key Generated:\n`{key}`\nValid for {days} days.",
        parse_mode="Markdown"
    )

async def check_expired(context: ContextTypes.DEFAULT_TYPE):
    users = load_json(PREMIUM_FILE)
    expired = []

    for user_id, expiry_str in list(users.items()):
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
        if datetime.now() > expiry_date:
            expired.append(user_id)
            del users[user_id]
            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text="⚠️ Your Premium Has Ended 👋"
                )
            except:
                pass

    if expired:
        save_json(PREMIUM_FILE, users)

# === MAIN ===
app_ = ApplicationBuilder().token(BOT_TOKEN).build()

app_.add_handler(CommandHandler("start", start))
app_.add_handler(CommandHandler("redeem", redeem))
app_.add_handler(CommandHandler("genk", genk))
app_.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Daily expiry check
app_.job_queue.run_repeating(check_expired, interval=86400, first=10)

app_.run_polling()
