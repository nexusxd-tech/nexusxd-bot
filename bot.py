import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.error import Forbidden, BadRequest

# ============ CONFIG - EDIT THESE ============
BOT_TOKEN = "8625046082:AAE-DL7jBZxZ0EJImp4TM7xXTcmJLnFzQas" # 1. From @BotFather
OWNER_ID = 123456789  # 2. Your Telegram ID 
MUST_JOIN_GROUPS = ["@nexusxdtch_bot","@nexustch2","https://t.me/+4z7crzFd72RkNmVk"]     # 3. Your channel username
LOG_GROUP_ID = -8091041100  # 4. Your log group ID
# ============================================

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

user_ids = set()

def generate_safe_grid(mines_count):
    total_tiles = 25
    safe_count = 25 - mines_count
    tiles_to_show = min(5, safe_count)
    safe_positions = sorted(random.sample(range(total_tiles), tiles_to_show))
    grid = []
    for row in range(5):
        line = ""
        for col in range(5):
            pos = row * 5 + col
            line += "⭐️" if pos in safe_positions else "🟦"
        grid.append(line)
    return "\n".join(grid)

async def check_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for group in MUST_JOIN_GROUPS:
        try:
            member = await context.bot.get_chat_member(chat_id=group, user_id=user_id)
            if member.status in [ChatMember.LEFT, ChatMember.KICKED]:
                return False
        except:
            return False
    return True

def main_menu():
    keyboard = [
        [InlineKeyboardButton("⭐️ Safe: 1 Mine", callback_data="safe_1"),
         InlineKeyboardButton("⭐️ Safe: 3 Mines", callback_data="safe_3")],
        [InlineKeyboardButton("⭐️ Safe: 5 Mines", callback_data="safe_5"),
         InlineKeyboardButton("⭐️ Safe: 10 Mines", callback_data="safe_10")],
        [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{MUST_JOIN_GROUPS[0][1:]}")],
        [InlineKeyboardButton("🔄 Check Join", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def predict_menu(mines_count):
    keyboard = [
        [InlineKeyboardButton("🔮 New Safe Tiles", callback_data=f"safe_{mines_count}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_ids.add(user_id)
    await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"🆕 User: {user.first_name} | @{user.username} | `{user_id}`", parse_mode='Markdown')
    if not await check_joined(user_id, context):
        join_text = "\n".join(MUST_JOIN_GROUPS)
        await update.message.reply_text(f"🚫 *Access Denied*\n\nJoin our channels to get safe tiles:\n\n{join_text}\n\nClick 'Check Join' after joining.", reply_markup=main_menu(), parse_mode='Markdown')
        return
    welcome = f"╭─❏ 𝗡𝗘𝗫𝗨𝗦𝗫𝗗 𝗦𝗔𝗙𝗘 𝗧𝗜𝗟𝗘𝗦 ❏\n│ 🥀 Welcome {user.first_name}\n│ 🔥 System online & stable\n│ ⚙️ UPGRADE LIVE. AUTOMATE MORE. SCALE FAST.\n│\n│ ⭐️ Get safe tile positions\n│ 🔄 New pattern each time\n│\n╰─〔 ⚡ Powered by 𝗡𝗲𝘅𝘂𝘀𝗫𝗗™ ────"
    await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_ids.add(user_id)
    if query.data == "check_join":
        if await check_joined(user_id, context):
            await query.edit_message_text("✅ *Access Granted*\n\nSelect mines amount:", reply_markup=main_menu(), parse_mode='Markdown')
        else:
            await query.answer("❌ You haven't joined all channels yet!", show_alert=True)
    elif query.data == "main_menu":
        await query.edit_message_text("⭐️ *Select mine amount to get safe tiles:*", reply_markup=main_menu(), parse_mode='Markdown')
    elif query.data.startswith("safe_"):
        if not await check_joined(user_id, context):
            await query.edit_message_text("🚫 Join required channels first. Use /start")
            return
        mines_count = int(query.data.split("_")[1])
        grid_display = generate_safe_grid(mines_count)
        msg = f"✅ *Safe Tiles Located* ✅\n💣 *Mines on board:* {mines_count}\n\n{grid_display}\n\n_UPGRADE LIVE. AUTOMATE MORE. SCALE FAST._\nPowered by 𝗡𝗲𝘅𝘂𝘀𝗫𝗗™"
        await query.edit_message_text(msg, reply_markup=predict_menu(mines_count), parse_mode='Markdown')
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"⭐️ {query.from_user.first_name} got safe tiles for {mines_count} mines")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id!= OWNER_ID:
        await update.message.reply_text("❌ Only admin can broadcast.")
        return
    if not context.args:
        await update.message.reply_text("📢 *Usage:* `/broadcast Your message here`\n\nSends to all bot users.", parse_mode='Markdown')
        return
    message = " ".join(context.args)
    sent = 0
    failed = 0
    await update.message.reply_text(f"📡 Broadcasting to {len(user_ids)} users...")
    for uid in list(user_ids):
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 *NexusXD Announcement*\n\n{message}", parse_mode='Markdown')
            sent += 1
        except (Forbidden, BadRequest):
            user_ids.discard(uid)
            failed += 1
        except Exception as e:
            logger.error(f"Broadcast error to {uid}: {e}")
            failed += 1
    await update.message.reply_text(f"✅ *Broadcast Complete*\n\nSent: {sent}\nFailed: {failed}", parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= OWNER_ID:
        return
    await update.message.reply_text(f"📊 *Bot Stats*\n\nTotal Users: {len(user_ids)}", parse_mode='Markdown')

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("NexusXD Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()