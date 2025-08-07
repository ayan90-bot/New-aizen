from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import os

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Your Telegram user ID

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Aizen Bot ✨\nUse This Command /redeem")

# --- REDEEM ---
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("❌ Please provide a message after /redeem")
        return
    forward_text = f"🔔 New Redeem Request:\nFrom: {user.full_name} (@{user.username})\nUserID: {user.id}\n\nMessage:\n{msg}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=forward_text)
    await update.message.reply_text("Processing 🗝️")

# --- ADMIN REPLY ---
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        cmd, user_id, *reply_msg = update.message.text.split(maxsplit=2)
        user_id = int(user_id)
        reply_msg = ' '.join(reply_msg)
        await context.bot.send_message(chat_id=user_id, text=reply_msg)
        await update.message.reply_text("✅ Sent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# --- BROADCAST ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("❌ Usage: /broadcast Your message")
        return
    # In production, you should save user IDs in a DB. For now, we’ll use a file.
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            ids = list(set(int(i.strip()) for i in f.readlines()))
        for uid in ids:
            try:
                await context.bot.send_message(chat_id=uid, text=msg)
            except:
                pass
        await update.message.reply_text("📢 Broadcast complete.")

# --- TRACK USERS ---
async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    with open("users.txt", "a") as f:
        f.write(str(uid) + "\n")

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_user))

    print("🤖 Bot is running...")
    app.run_polling()
