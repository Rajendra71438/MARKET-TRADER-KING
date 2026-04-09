import os
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
    with open(USERS_FILE, "a+") as f:
        f.seek(0)
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

def get_users():
    try:
        with open(USERS_FILE, "r") as f:
            return f.read().splitlines()
    except:
        return []

# ---------------- CHANNELS ----------------
def save_channel(channel_id):
    with open(CHANNELS_FILE, "a+") as f:
        f.seek(0)
        channels = f.read().splitlines()
        if str(channel_id) not in channels:
            f.write(f"{channel_id}\n")

def get_channels():
    try:
        with open(CHANNELS_FILE, "r") as f:
            return f.read().splitlines()
    except:
        return []

# ---------------- JOIN REQUEST (YOUR ORIGINAL LOGIC) ----------------
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.chat_join_request.from_user.id

    save_user(user_id)  # added for stats/broadcast

    try:
        await context.bot.copy_message(user_id, CHANNEL_ID, WELCOME_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, VIDEO_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, APK_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, VOICE_MSG_ID)

    except Exception as e:
        print(e)

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
        users = len(get_users())
        channels = len(get_channels())

        await query.message.reply_text(
            f"📊 Stats\n\n👤 Users: {users}\n📡 Channels: {channels}"
        )

    elif query.data == "channels":
        channels = get_channels()

        if not channels:
            await query.message.reply_text("No channels found.")
            return

        text = "📡 Channels:\n\n"
        for c in channels:
            text += f"`{c}`\n"

        await query.message.reply_text(text, parse_mode="Markdown")

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
        except:
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast Done\n\nSent: {sent}\nFailed: {failed}"
    )

# ---------------- APP ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Your original handler
app.add_handler(ChatJoinRequestHandler(handle_join))

# Track channels
app.add_handler(ChatMemberHandler(track_bot, ChatMemberHandler.MY_CHAT_MEMBER))

# Admin
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(button_handler))

# Broadcast messages
app.add_handler(MessageHandler(filters.ALL, handle_broadcast))

print("🚀 Bot running...")
app.run_polling()
