from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from datetime import datetime, timedelta
import pytz

from info import ADMINS, LOG_CHANNEL  
from database import db  

@Client.on_message(filters.command("addpremium") & filters.user(ADMINS))
async def add_premium(client, message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("❌ Usage: /addpremium <user_id> [days]")
        
        user_id = int(args[1])
        days = int(args[2]) if len(args) > 2 else 30

        tz = pytz.timezone("Asia/Kolkata")
        expire = datetime.now(tz) + timedelta(days=days)
        date_var, time_var = str(expire).split(" ")
        await db.update_verification(user_id, date_var, time_var)

        # Admin confirmation
        await message.reply(
            f"✅ Added premium to user `{user_id}` for {days} days.\n"
            f"⏳ Expires on **{date_var} {time_var}**."
        )

        # Log in channel
        try:
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=(
                    f"📢 **Premium Activated**\n\n"
                    f"👤 User ID: `{user_id}`\n"
                    f"⏳ Valid for: `{days} days`\n"
                    f"🕒 Expires on: `{date_var} {time_var}`\n"
                    f"🔧 Activated by: [{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                )
            )
        except Exception as log_error:
            await message.reply(f"⚠️ Failed to log to channel: `{log_error}`")

        # Notify the user
        try:
            await client.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 Congratulations!\n\n"
                    f"💎 You’ve been upgraded to **Premium** for **{days} days**.\n"
                    f"⏳ Expires on: `{date_var} {time_var}`\n\n"
                    f"Enjoy your ad-free, enhanced experience! 🥳"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Check Premium", callback_data="check_premium")],
                    [InlineKeyboardButton("📩 Contact Support", url=f"https://t.me/MyselfPrincess")]
                ])
            )
        except Exception as notify_error:
            await message.reply(f"⚠️ Couldn't notify the user: `{notify_error}`")
    except Exception as e:
        await message.reply(f"⚠️ Error: `{e}`")
        
@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(client, message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("❌ Usage: /removepremium <user_id>")
        user_id = int(args[1])
        await db.update_verification(user_id, "1999-12-31", "23:59:59")
        await message.reply(f"✅ Removed premium for user `{user_id}`.")
    except Exception as e:
        await message.reply(f"⚠️ Error: `{e}`")

@Client.on_message(filters.command("checkpremium"))
async def check_premium(client, message):
    try:
        args = message.text.split()
        sender_id = message.from_user.id
        sender_name = message.from_user.mention
        is_admin = sender_id in ADMINS

        # Get target user_id (from argument or self)
        if len(args) == 1:
            user_id = sender_id
        else:
            user_id = int(args[1])
            if not is_admin and user_id != sender_id:
                return await message.reply("❌ You are not allowed to check other users' premium status.")

        # Fetch user status
        status = await db.get_verified(user_id)
        exp = datetime.strptime(status["date"] + " " + status["time"], "%Y-%m-%d %H:%M:%S")
        is_active = exp > datetime.now(pytz.timezone("Asia/Kolkata"))

        # Reply
        await message.reply(
            f"👤 User: `{user_id}` {'(' + sender_name + ')' if user_id == sender_id else ''}\n"
            f"💎 Premium: {'✅ Active' if is_active else '❌ Expired'}\n"
            f"⏳ Expires on: `{status['date']} {status['time']}`"
        )

    except Exception as e:
        await message.reply(f"⚠️ Error: `{e}`")
        
@Client.on_message(filters.command("buypremium") & filters.private)
async def buy_premium_info(client, message):
    await message.reply(
        "💎 **Buy Premium Access**\n\n"
        "✨ Benefits:\n"
        "• Ad-Free Experience\n"
        "• Early Access to Features\n"
        "• Priority Support\n\n"
        "💰 Pricing:\n"
        "• 30 Days – ₹49\n"
        "• 90 Days – ₹99\n"
        "• Lifetime – ₹199\n\n"
        "📲 Contact @YourSupportUsername to upgrade."
    )
    
