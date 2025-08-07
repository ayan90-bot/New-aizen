import os
import threading
import random
import string
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# === Flask for 24/7 Uptime (UptimeRobot ping support) ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Aizen Bot Alive 💀"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Aizen Bot ✨\nUse This Command /redeem")

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

    with open("users.txt", "a") as f:
        f.write(f"{user.id}\n")

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

# === /broadcast ===
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("❌ Usage: /broadcast your message")
        return

    sent, failed = 0, 0
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            ids = set(int(i.strip()) for i in f if i.strip().isdigit())

        for uid in ids:
            try:
                await context.bot.send_message(chat_id=uid, text=msg)
                sent += 1
            except:
                failed += 1

    await update.message.reply_text(f"📢 Broadcast done. Sent: {sent}, Failed: {failed}")

# === /genk (Generate Premium Key) ===
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def genk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    key = generate_key()
    with open("keys.txt", "a") as f:
        f.write(f"{key}\n")

    await update.message.reply_text(f"🗝️ Generated Key: `{key}`", parse_mode="Markdown")

# === /premium (Use Premium Key) ===
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please enter a key like: /premium YOUR_KEY")
        return

    input_key = context.args[0].strip().upper()

    if not os.path.exists("keys.txt"):
        await update.message.reply_text("❌ Invalid Key")
        return

    with open("keys.txt", "r") as f:
        keys = [k.strip() for k in f.readlines()]

    if input_key in keys:
        # Remove used key
        keys.remove(input_key)
        with open("keys.txt", "w") as f:
            for k in keys:
                f.write(k + "\n")
        await update.message.reply_text("✅ Access Granted. Welcome to Premium 🔥")
    else:
        await update.message.reply_text("❌ Invalid Key")

# === MAIN RUNNER ===
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("premium", premium))

    # Admin Commands
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("genk", genk))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
