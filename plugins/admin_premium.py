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

        expiry_date, expiry_time = await premium_user(client, user_id, days)

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

# 👤 User Command - Check Own Premium
@Client.on_message(filters.command("mypremium"))
async def my_premium(client, message: Message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.mention

        # Fetch premium data
        status = await db.get_verified(user_id)
        if not status:
            return await message.reply("⚠️ No premium data found for you.")

        tz = pytz.timezone("Asia/Kolkata")
        exp_dt = tz.localize(datetime.strptime(status["date"] + " " + status["time"], "%Y-%m-%d %H:%M:%S"))
        now = datetime.now(tz)

        # Status check
        is_active = exp_dt > now
        activation_dt = tz.localize(datetime.strptime(status["activation_date"] + " " + status["activation_time"], "%Y-%m-%d %H:%M:%S")) \
            if "activation_date" in status and "activation_time" in status else None

        not_premium = False
        if activation_dt:
            total_duration = (exp_dt - activation_dt).days
            if total_duration <= 7:
                not_premium = True

        # Time left
        if is_active and not not_premium:
            delta = exp_dt - now
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            time_left = f"{days}d {hours}h {minutes}m"
        elif not_premium:
            time_left = "Not Premium 🚫"
        else:
            time_left = "Expired ❌"

        expires_on = exp_dt.strftime("%d/%m/%Y, %I:%M %p")

        await message.reply(
            f"👤 **User:** {user_name}\n"
            f"💎 **Premium Status:** "
            f"{'😄 Active' if is_active and not not_premium else ('🚫 Not Premium' if not_premium else '😔 Expired')}\n"
            f"📌 **Expires:** `{expires_on}`\n"
            f"⏳ **Time Left:** `{time_left}`"
        )

    except Exception as e:
        await message.reply(f"⚠️ Error: `{e}`")


# 🛠️ Admin Command - Check Any User Premium
@Client.on_message(filters.command("checkpremium") & filters.user(ADMINS))
async def check_premium(client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("❌ Usage: /checkuserpremium user_id")

        user_id = int(args[1])
        try:
            target = await client.get_users(user_id)
            user_name = target.mention
        except:
            user_name = "Unknown"

        status = await db.get_verified(user_id)
        if not status:
            return await message.reply("⚠️ No premium data found for this user.")

        tz = pytz.timezone("Asia/Kolkata")
        exp_dt = tz.localize(datetime.strptime(status["date"] + " " + status["time"], "%Y-%m-%d %H:%M:%S"))
        now = datetime.now(tz)

        # Status check
        is_active = exp_dt > now
        activation_dt = tz.localize(datetime.strptime(status["activation_date"] + " " + status["activation_time"], "%Y-%m-%d %H:%M:%S")) \
            if "activation_date" in status and "activation_time" in status else None

        not_premium = False
        if activation_dt:
            total_duration = (exp_dt - activation_dt).days
            if total_duration <= 7:
                not_premium = True

        # Time left
        if is_active and not not_premium:
            delta = exp_dt - now
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            time_left = f"{days}d {hours}h {minutes}m"
        elif not_premium:
            time_left = "Not Premium 🚫"
        else:
            time_left = "Expired ❌"

        expires_on = exp_dt.strftime("%d/%m/%Y, %I:%M %p")

        await message.reply(
            f"👤 **User:** `{user_id}` ({user_name})\n"
            f"💎 **Premium Status:** "
            f"{'😄 Active' if is_active and not not_premium else ('🚫 Not Premium' if not_premium else '😔 Expired')}\n"
            f"📌 **Expires:** `{expires_on}`\n"
            f"⏳ **Time Left:** `{time_left}`"
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
    
