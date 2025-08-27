from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from datetime import datetime, timedelta
import pytz

from info import ADMINS, LOG_CHANNEL
from database.users_chats_db import db


TZ = pytz.timezone("Asia/Kolkata")


# ------------------------------
# Premium Logging
# ------------------------------
async def log_premium_action(client, action: str, target_user: int, days: int = None, admin: int = None):
    try:
        now = datetime.now(TZ).strftime("%d %B %Y, %I:%M %p")

        # fetch user and admin info
        try:
            target = await client.get_users(target_user)
            target_name = f"{target.first_name or ''} {target.last_name or ''}".strip()
            target_username = f"@{target.username}" if target.username else "❌"
        except Exception:
            target_name, target_username = "Unknown", "❌"

        try:
            admin_user = await client.get_users(admin)
            admin_name = f"{admin_user.first_name or ''} {admin_user.last_name or ''}".strip()
            admin_username = f"@{admin_user.username}" if admin_user.username else "❌"
        except Exception:
            admin_name, admin_username = "Unknown", "❌"

        # calculate expiry
        try:
            days_left = await db.get_premium_days_left(target_user) or 0
            expiry = datetime.now(TZ) + timedelta(days=int(days_left))
            expiry_str = expiry.strftime("%d %B %Y, %I:%M %p")
        except Exception:
            days_left, expiry_str = "?", "Unknown"

        if action == "add":
            text = (
                f"#PremiumAdded ✅\n\n"
                f"👤 **User:** {target_name} (`{target_user}`)\n"
                f"🔗 Username: {target_username}\n\n"
                f"📅 Days Added: **{days}**\n"
                f"⏳ Days Left: **{days_left}**\n"
                f"🗓 Expiry: **{expiry_str}**\n\n"
                f"🛠 **By Admin:** {admin_name} (`{admin}`)\n"
                f"🔗 Username: {admin_username}\n\n"
                f"📌 Time: {now}"
            )
        elif action == "edit":
            text = (
                f"#PremiumEdited ✏️\n\n"
                f"👤 **User:** {target_name} (`{target_user}`)\n"
                f"🔗 Username: {target_username}\n\n"
                f"🆕 New Days: **{days}**\n"
                f"⏳ Days Left: **{days_left}**\n"
                f"🗓 Expiry: **{expiry_str}**\n\n"
                f"🛠 **By Admin:** {admin_name} (`{admin}`)\n"
                f"🔗 Username: {admin_username}\n\n"
                f"📌 Time: {now}"
            )
        elif action == "extend":
            text = (
                f"#PremiumExtended ➕\n\n"
                f"👤 **User:** {target_name} (`{target_user}`)\n"
                f"🔗 Username: {target_username}\n\n"
                f"➕ Added Days: **{days}**\n"
                f"⏳ Days Left: **{days_left}**\n"
                f"🗓 Expiry: **{expiry_str}**\n\n"
                f"🛠 **By Admin:** {admin_name} (`{admin}`)\n"
                f"🔗 Username: {admin_username}\n\n"
                f"📌 Time: {now}"
            )
        elif action == "remove":
            text = (
                f"#PremiumRemoved 🚫\n\n"
                f"👤 **User:** {target_name} (`{target_user}`)\n"
                f"🔗 Username: {target_username}\n\n"
                f"⏳ Days Left Before Removal: **{days_left}**\n"
                f"🗓 Expiry: **{expiry_str}**\n\n"
                f"🛠 **By Admin:** {admin_name} (`{admin}`)\n"
                f"🔗 Username: {admin_username}\n\n"
                f"📌 Time: {now}"
            )
        else:
            text = f"#UnknownAction ❓\nAdmin `{admin}` → User `{target_user}` at {now}"

        await client.send_message(LOG_CHANNEL, text)

    except Exception:
        pass


# ------------------------------
# Add Premium
# ------------------------------
@Client.on_message(filters.command("addpremium") & filters.user(ADMINS))
async def add_premium(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return await message.reply("⚠️ Usage: /addpremium user_id days")

        user_id = int(args[1])
        input_days = int(args[2])
        if input_days <= 0:
            return await message.reply("⚠️ Days must be a positive number.")

        if await db.is_premium(user_id):
            days_left = await db.get_premium_days_left(user_id) or 0
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("➕ Add More Days", callback_data=f"add_days:{user_id}:{input_days}"),
                        InlineKeyboardButton("✏️ Edit Premium Days", callback_data=f"edit_days:{user_id}:{input_days}"),
                    ],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")],
                ]
            )
            return await message.reply(
                f"⚠️ User `{user_id}` already premium.\n⏳ Days left: **{days_left}**\n\nChoose an action:",
                reply_markup=keyboard,
            )

        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("✅ Confirm Add Premium", callback_data=f"confirm_add:{user_id}:{input_days}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
            ]]
        )
        await message.reply(
            f"🤔 User `{user_id}` is not premium.\nAdd for **{input_days} days**?",
            reply_markup=keyboard,
        )
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ------------------------------
# Remove Premium
# ------------------------------
@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("⚠️ Usage: /removepremium user_id")

        user_id = int(args[1])
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("✅ Confirm Remove", callback_data=f"confirm_remove:{user_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
            ]]
        )
        await message.reply(
            f"⚠️ Remove premium from user `{user_id}`?",
            reply_markup=keyboard,
        )
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ------------------------------
# Premium Stats
# ------------------------------
@Client.on_message(filters.command("totalpremium") & filters.user(ADMINS))
async def total_premium(client: Client, message: Message):
    total = await db.total_premium_users_count()
    await message.reply(f"📊 Total premium users: **{total}**")


@Client.on_message(filters.command("activepremium") & filters.user(ADMINS))
async def active_premium(client: Client, message: Message):
    active = await db.total_active_premium_users_count()
    await message.reply(f"🔥 Active premium users: **{active}**")


# ------------------------------
# Callback Actions
# ------------------------------
@Client.on_callback_query(filters.regex(r"^(add_days|edit_days|confirm_add|confirm_remove):"))
async def premium_actions(client: Client, cq: CallbackQuery):
    try:
        if cq.from_user.id not in ADMINS:
            return await cq.answer("Not allowed.", show_alert=True)

        data = cq.data.split(":")
        action = data[0]
        user_id = int(data[1])

        if action in ("add_days", "edit_days", "confirm_add"):
            days = int(data[2])
            if days <= 0:
                return await cq.answer("Days must be positive.", show_alert=True)

            if action == "add_days":
                left = await db.get_premium_days_left(user_id) or 0
                total_days = left + days
                await db.add_premium(user_id, total_days)
                await cq.message.edit_text(f"✅ Added {days} days.\nTotal: {total_days} days.")
                await cq.answer("Premium extended!")
                await log_premium_action(client, "extend", user_id, days, cq.from_user.id)

            elif action == "edit_days":
                await db.add_premium(user_id, days)
                await cq.message.edit_text(f"✏️ Updated premium to {days} days.")
                await cq.answer("Premium updated!")
                await log_premium_action(client, "edit", user_id, days, cq.from_user.id)

            elif action == "confirm_add":
                await db.add_premium(user_id, days)
                await cq.message.edit_text(f"✅ Premium activated for {days} days.")
                await cq.answer("Premium added!")
                await log_premium_action(client, "add", user_id, days, cq.from_user.id)

        elif action == "confirm_remove":
            await db.remove_premium(user_id)
            await cq.message.edit_text(f"🚫 Premium removed from {user_id}.")
            await cq.answer("Premium removed!")
            await log_premium_action(client, "remove", user_id, None, cq.from_user.id)

    except Exception as e:
        try:
            await cq.message.edit_text(f"❌ Error: {e}")
        except:
            pass


# ------------------------------
# Cancel Action
# ------------------------------
@Client.on_callback_query(filters.regex(r"^cancel_action$"))
async def cancel_action(client: Client, cq: CallbackQuery):
    await cq.answer("❌ Cancelled!")
    try:
        await cq.message.edit_text("❌ Action cancelled.")
    except:
        pass


# ------------------------------
# Check Premium (command + button)
# ------------------------------
@Client.on_message(filters.command("checkpremium"))
async def check_premium_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if await db.is_premium(user_id):
        days = await db.get_premium_days_left(user_id) or 0
        expiry = datetime.now(TZ) + timedelta(days=int(days))
        expiry_str = expiry.strftime("%d %B %Y, %I:%M %p")
        text = (
            f"🌟 **Premium Status** 🌟\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"✨ Status: ✅ Active\n"
            f"⏳ Days Left: **{days}**\n"
            f"📅 Expiry Date: **{expiry_str}**"
        )
        await message.reply(text)
    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium")],
             [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]
        )
        await message.reply("😢 You are not a premium user.\n💡 Upgrade now!", reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^check_premium_user$"))
async def check_premium_btn(client: Client, cq: CallbackQuery):
    user_id = cq.from_user.id
    if await db.is_premium(user_id):
        days = await db.get_premium_days_left(user_id) or 0
        expiry = datetime.now(TZ) + timedelta(days=int(days))
        expiry_str = expiry.strftime("%d %B %Y, %I:%M %p")
        text = (
            f"🌟 **Premium Status** 🌟\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"✨ Status: ✅ Active\n"
            f"⏳ Days Left: **{days}**\n"
            f"📅 Expiry Date: **{expiry_str}**"
        )
        await cq.message.reply(text)
    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium")],
             [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]
        )
        await cq.message.reply("😢 You are not a premium user.\n💡 Upgrade now!", reply_markup=keyboard)


# ------------------------------
# Buy Premium
# ------------------------------
@Client.on_callback_query(filters.regex(r"^buy_premium$"))
async def buy_premium(client: Client, cq: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("👨‍💻 Contact Admin", url="https://t.me/YourAdminUsername")],
         [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]
    )
    await cq.message.reply("💎 To buy premium, contact admin.", reply_markup=keyboard)
    
