from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from datetime import datetime, timedelta
import pytz
from utils import premium_user, update_verify_status
from info import ADMINS, LOG_CHANNEL  
from database.users_chats_db import db

@Client.on_message(filters.command("addpremium") & filters.user(ADMINS))
async def add_premium(client, message: Message):
    try:
        args = message.text.split()

        if len(args) < 2:
            return await message.reply("❌ Usage: `/addpremium user_id [days]`", quote=True)

        user_id = int(args[1])
        days = int(args[2]) if len(args) > 2 else 30
        hours = days * 24

        expiry_date, expiry_time = await premium_user(client, user_id, hours)

        if not expiry_date:
            return await message.reply("❌ Failed to upgrade user to premium.", quote=True)
        await message.reply(
            f"✅ Premium added to user `{user_id}` for {days} days.\n"
            f"⏳ Expires on **{expiry_date} {expiry_time}**."
        )
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=(
                f"📢 **Premium Activated**\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"⏳ Valid for: `{days} days`\n"
                f"🕒 Expires on: `{expiry_date} {expiry_time}`\n"
                f"🔧 Activated by: [{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            )
        )
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Congratulations!\n\n"
                f"💎 You’ve been upgraded to **Premium** for **{days} days**.\n"
                f"⏳ Expires on: `{expiry_date} {expiry_time}`\n\n"
                f"Enjoy your ad-free, enhanced experience! 🥳"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Check Premium", callback_data="check_premium")],
                [InlineKeyboardButton("📩 Contact Support", url="https://t.me/MyselfPrincess")]
            ])
        )

    except Exception as e:
        await message.reply(f"⚠️ Error: `{str(e)}`", quote=True)
        
@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("❌ Usage: /removepremium user_id")
        user_id = int(args[1])
        date_temp = "1999-12-31"
        time_temp = "23:59:59"
        await update_verify_status(client, user_id, date_temp, time_temp)
        await message.reply(f"✅ Removed premium for user `{user_id}`.")
    except Exception as e:
        await message.reply(f"⚠️ Error: `{e}`")

@Client.on_message(filters.command(["checkpremium", "checkverification"]))
async def check_premium(client, message: Message):
    try:
        args = message.text.split()
        sender_id = message.from_user.id
        sender_name = message.from_user.mention
        is_admin = sender_id in ADMINS

        if len(args) > 1:
            if not is_admin:
                return await message.reply("❌ You are not allowed to check other users' status.")
            user_id = int(args[1])
        else:
            user_id = sender_id

        # Fetch user data from DB
        data = await db.get_verified(user_id)
        date_str = data.get('date', "1999-12-31")
        time_str = data.get('time', "23:59:59")
        tz = pytz.timezone("Asia/Kolkata")

        # Handle unverified users
        if date_str == "1999-12-31" and time_str == "23:59:59":
            return await message.reply("🟡 User has not verified yet.")

        # Parse date & time
        verified_dt = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
        verification_expiry = verified_dt + timedelta(hours=12)
        premium_expiry = verified_dt
        now = datetime.now(tz)
        verification_active = verification_expiry > now
        premium_active = premium_expiry > now

        if verification_active:
            verification_time_left = str(verification_expiry - now).split(".")[0]  # hh:mm:ss
        else:
            verification_time_left = "Expired"
        def fmt(dt):
            return dt.strftime("%d %b %Y, %I:%M:%S %p IST") if USE_12_HOUR_FORMAT else dt.strftime("%d %b %Y, %H:%M:%S IST")

        verified_fmt = fmt(verified_dt)
        verification_exp_fmt = fmt(verification_expiry)
        premium_exp_fmt = fmt(premium_expiry)

        # Reply message
        await message.reply(
            f"👤 **User**: `{user_id}` {'(' + sender_name + ')' if user_id == sender_id else ''}\n"
            f"💎 **Premium**: {'✅ Active' if premium_active else '❌ Expired'}\n"
            f"🗓️ Premium Expires: `{premium_exp_fmt}`\n\n"
            f"✅ **Verification**: {'Active' if verification_active else 'Expired'}\n"
            f"🗓️ Verified On: `{verified_fmt}`\n"
            f"📌 Verification Expires: `{verification_exp_fmt}`\n"
            f"⏳ Time Left: `{verification_time_left}`"
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
    
