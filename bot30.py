import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
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


def remove_channel(channel_id):
    channels = get_channels()
    channels = [c for c in channels if c != str(channel_id)]
    with open(CHANNELS_FILE, "w") as f:
        for c in channels:
            f.write(c + "\n")


# ---------------- JOIN REQUEST ----------------
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    user_id = user.id

    # save user
    save_user(user_id)

    try:
        # ✅ auto approve user
        await update.chat_join_request.approve()

        # ✅ send 4 messages
        await context.bot.copy_message(user_id, CHANNEL_ID, WELCOME_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, VIDEO_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, APK_MSG_ID)
        await context.bot.copy_message(user_id, CHANNEL_ID, VOICE_MSG_ID)

        # ✅ notify admin (optional)
        await context.bot.send_message(
            ADMIN_ID,
            f"👤 New User:\nName: {user.full_name}\nID: {user_id}"
        )

    except Exception as e:
        print(f"ERROR for {user_id}: {e}")


# ---------------- TRACK CHANNEL ----------------
async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.my_chat_member.chat

    if chat.type == "channel":
        save_channel(chat.id)


# ---------------- STATS ----------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    users = len(get_users())
    channels = len(get_channels())

    await update.message.reply_text(
        f"📊 Stats:\n\n👤 Users: {users}\n📡 Channels: {channels}"
    )


# ---------------- BROADCAST STEP 1 ----------------
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    broadcast_mode.add(update.effective_user.id)
    await update.message.reply_text("✉️ Send message to broadcast")


# ---------------- BROADCAST STEP 2 ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# ---------------- CHANNEL LIST ----------------
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    channels = get_channels()

    if not channels:
        await update.message.reply_text("No channels found.")
        return

    text = "📡 Channels:\n\n"
    for c in channels:
        text += f"`{c}`\n"

    await update.message.reply_text(text, parse_mode="Markdown")


# ---------------- REMOVE CHANNEL ----------------
async def remove_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage:\n/removechannel CHANNEL_ID")
        return

    remove_channel(context.args[0])
    await update.message.reply_text("❌ Channel removed")


# ---------------- APP ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(ChatJoinRequestHandler(handle_join))
app.add_handler(ChatMemberHandler(track_bot, ChatMemberHandler.MY_CHAT_MEMBER))

app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast_cmd))
app.add_handler(CommandHandler("channels", list_channels))
app.add_handler(CommandHandler("removechannel", remove_channel_cmd))

app.add_handler(MessageHandler(filters.ALL, handle_message))

print("🚀 Bot running...")
app.run_polling()