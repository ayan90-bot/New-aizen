import os
import threading
import random
import string
import json
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# === Flask for UptimeRobot ping ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Aizen Bot Alive 💀"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# === Files ===
KEYS_FILE = "keys.json"
PREMIUM_USERS_FILE = "premium_users.json"

for file in [KEYS_FILE, PREMIUM_USERS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Aizen Bot ✨\n"
        "Use This Command /redeem\n"
        "How to use Bot /htub"
    )

# === /htub ===
async def htub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "1. /redeem Enter Your Account Details 🧑‍💻\n\n"
        "Example 🤖 /redeem aizen@gmail.com:Aizen\n\n"
        "We Provide Only Prime Video — Other Services Add Soon 🔜"
    )
    await update.message.reply_text(msg)

# === /redeem ===
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("❌ Please provide a message after /redeem")
        return

    forward_text = f"🔔 New Redeem Request:\nFrom: {user.full_name} (@{user.username})\nUserID: {user.id}\n\nMessage:\n{msg}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=forward_text)
    await update.message.reply_text("Processing 🗝️")

# === /reply ===
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        parts = update.message.text.split(maxsplit=2)
        if len(parts) < 3:
            await update.message.reply_text("❌ Format: /reply <user_id> <message>")
            return

        _, user_id_str, reply_msg = parts
        user_id = int(user_id_str)

        await context.bot.send_message(chat_id=user_id, text=reply_msg)
        await update.message.reply_text("✅ Sent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# === /genk ===
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def genk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        days = int(context.args[0]) if context.args else 7
        key = generate_key()
        valid_till = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        with open(KEYS_FILE, 'r+') as f:
            keys = json.load(f)
            keys[key] = {"user_id": None, "valid_till": valid_till}
            f.seek(0)
            json.dump(keys, f, indent=2)
            f.truncate()

        await update.message.reply_text(f"🗝️ Generated Key: `{key}`\nValid Till: {valid_till}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# === /premium ===
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("❌ Please enter a key like: /premium YOUR_KEY")
        return

    input_key = context.args[0].strip().upper()

    with open(KEYS_FILE, 'r+') as f:
        keys = json.load(f)

        if input_key not in keys:
            await update.message.reply_text("❌ Invalid Key")
            return

        key_data = keys[input_key]
        if key_data["user_id"] is not None:
            await update.message.reply_text("❌ Key already used")
            return

        keys[input_key]["user_id"] = user.id

        with open(PREMIUM_USERS_FILE, 'r+') as pf:
            premium_users = json.load(pf)
            premium_users[str(user.id)] = keys[input_key]["valid_till"]
            pf.seek(0)
            json.dump(premium_users, pf, indent=2)
            pf.truncate()

        f.seek(0)
        json.dump(keys, f, indent=2)
        f.truncate()

        # Notify admin when premium activated
        notify = (
            f"✅ PREMIUM ACTIVATED\n"
            f"User: {user.full_name} (@{user.username})\n"
            f"UserID: {user.id}\n"
            f"Key: {input_key}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=notify)

        await update.message.reply_text("✅ Premium Activated Successfully 🔥")

# === /checkpremium ===
async def checkpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    with open(PREMIUM_USERS_FILE, 'r') as f:
        users = json.load(f)

    if user_id in users:
        expiry = users[user_id]
        if datetime.strptime(expiry, '%Y-%m-%d') < datetime.now():
            await update.message.reply_text("❌ Your premium has ended 👋")
        else:
            await update.message.reply_text(f"✅ Premium Active till {expiry}")
    else:
        await update.message.reply_text("❌ You are not a premium user")

# === Main Runner ===
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("htub", htub))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(CommandHandler("checkpremium", checkpremium))
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(CommandHandler("genk", genk))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
