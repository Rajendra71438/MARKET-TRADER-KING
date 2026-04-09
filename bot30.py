import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ChatMemberHandler
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

WELCOME_MSG_ID = int(os.getenv("WELCOME_MSG_ID"))
VIDEO_MSG_ID = int(os.getenv("VIDEO_MSG_ID"))
APK_MSG_ID = int(os.getenv("APK_MSG_ID"))
VOICE_MSG_ID = int(os.getenv("VOICE_MSG_ID"))

USERS_FILE = "users.txt"
CHANNELS_FILE = "channels.txt"

broadcast_mode = set()

# ---------------- USERS ----------------
def save_user(user_id):
    users = get_users()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

def get_users():
    try:
        with open(USERS_FILE, "r") as f:
            return list(set([u.strip() for u in f if u.strip().isdigit()]))
    except:
        return []

def remove_user(user_id):
    users = get_users()
    users = [u for u in users if u != str(user_id)]
    with open(USERS_FILE, "w") as f:
        for u in users:
            f.write(f"{u}\n")

# ---------------- CHANNELS ----------------
def save_channel(channel_id):
    channels = get_channels()
    if str(channel_id) not in channels:
        with open(CHANNELS_FILE, "a") as f:
            f.write(f"{channel_id}\n")

def get_channels():
    try:
        with open(CHANNELS_FILE, "r") as f:
            return f.read().splitlines()
    except:
        return []

# ---------------- START (IMPORTANT FIX) ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)

    await update.message.reply_text("✅ You are registered! Now you can join the channel.")

# ---------------- JOIN REQUEST ----------------
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.chat_join_request.from_user.id

    save_user(user_id)

    try:
        await context.bot.copy_message(user_id, CHANNEL_ID, WELCOME_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, VIDEO_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, APK_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, VOICE_MSG_ID)
    except Exception as e:
        print(f"Join message failed for {user_id}: {e}")

# ---------------- TRACK CHANNELS ----------------
async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.my_chat_member.chat
    if chat.type == "channel":
        save_channel(chat.id)

# ---------------- ADMIN PANEL ----------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("📡 Channels", callback_data="channels")],
        [InlineKeyboardButton("✉️ Broadcast", callback_data="broadcast")]
    ]

    await update.message.reply_text(
        "⚙️ Admin Panel",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- BUTTON HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "stats":
        await query.message.reply_text(
            f"📊 Stats\n\n👤 Users: {len(get_users())}\n📡 Channels: {len(get_channels())}"
        )

    elif query.data == "channels":
        channels = get_channels()
        text = "\n".join(channels) if channels else "No channels found."
        await query.message.reply_text(text)

    elif query.data == "broadcast":
        broadcast_mode.add(query.from_user.id)
        await query.message.reply_text("✉️ Send message to broadcast")

# ---------------- BROADCAST ----------------
async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in broadcast_mode:
        return

    broadcast_mode.remove(user_id)

    users = get_users()
    sent = 0
    failed = 0

    for u in users:
        try:
            await context.bot.copy_message(
                chat_id=int(u),
                from_chat_id=update.effective_chat.id,
                message_id=update.message.id
            )
            sent += 1
            await asyncio.sleep(0.05)

        except Exception as e:
            print(f"Removing {u}: {e}")
            remove_user(u)
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast Done\n\nSent: {sent}\nFailed: {failed}"
    )

# ---------------- APP ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(ChatJoinRequestHandler(handle_join))
app.add_handler(ChatMemberHandler(track_bot, ChatMemberHandler.MY_CHAT_MEMBER))

app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.ALL, handle_broadcast))

print("🚀 Bot running...")
app.run_polling()
