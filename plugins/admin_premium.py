from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta
import pytz

from info import ADMINS, LOG_CHANNEL
from database.users_chats_db import db
from scripts import script   # import big texts

TZ = pytz.timezone("Asia/Kolkata")


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
                script.ADD_PREMIUM_ALREADY.format(id=user_id, days=days_left),
                reply_markup=keyboard,
            )

        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("✅ Confirm Add Premium", callback_data=f"confirm_add:{user_id}:{input_days}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
            ]]
        )
        await message.reply(
            script.ADD_PREMIUM_CONFIRM.format(id=user_id, days=input_days),
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
            script.REMOVE_PREMIUM_CONFIRM.format(id=user_id),
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
    await message.reply(script.TOTAL_PREMIUM.format(total))


@Client.on_message(filters.command("activepremium") & filters.user(ADMINS))
async def active_premium(client: Client, message: Message):
    active = await db.total_active_premium_users_count()
    await message.reply(script.ACTIVE_PREMIUM.format(active))


# ------------------------------
# Callback Actions (with inline logging)
# ------------------------------
@Client.on_callback_query(filters.regex(r"^(add_days|edit_days|confirm_add|confirm_remove):"))
async def premium_actions(client: Client, cq: CallbackQuery):
    try:
        if cq.from_user.id not in ADMINS:
            return await cq.answer("Not allowed.", show_alert=True)

        data = cq.data.split(":")
        action = data[0]
        user_id = int(data[1])
        now = datetime.now(TZ).strftime("%d %B %Y, %I:%M %p")

        # get admin details
        admin_user = cq.from_user
        admin_name = f"{admin_user.first_name or ''} {admin_user.last_name or ''}".strip()
        admin_username = f"@{admin_user.username}" if admin_user.username else "❌"

        # get target user info
        try:
            target = await client.get_users(user_id)
            target_name = f"{target.first_name or ''} {target.last_name or ''}".strip()
            target_username = f"@{target.username}" if target.username else "❌"
        except:
            target_name, target_username = "Unknown", "❌"

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

                expiry = datetime.now(TZ) + timedelta(days=total_days)
                expiry_str = expiry.strftime("%d %B %Y, %I:%M %p")
                text = script.PREMIUM_EXTENDED.format(
                    name=target_name, id=user_id, username=target_username,
                    days=days, left=total_days, expiry=expiry_str,
                    admin_name=admin_name, admin_id=cq.from_user.id, admin_username=admin_username,
                    time=now
                )
                await client.send_message(LOG_CHANNEL, text)

            elif action == "edit_days":
                await db.add_premium(user_id, days)
                await cq.message.edit_text(f"✏️ Updated premium to {days} days.")
                await cq.answer("Premium updated!")

                expiry = datetime.now(TZ) + timedelta(days=days)
                expiry_str = expiry.strftime("%d %B %Y, %I:%M %p")
                text = script.PREMIUM_EDITED.format(
                    name=target_name, id=user_id, username=target_username,
                    days=days, left=days, expiry=expiry_str,
                    admin_name=admin_name, admin_id=cq.from_user.id, admin_username=admin_username,
                    time=now
                )
                await client.send_message(LOG_CHANNEL, text)

            elif action == "confirm_add":
                await db.add_premium(user_id, days)
                await cq.message.edit_text(f"✅ Premium activated for {days} days.")
                await cq.answer("Premium added!")

                expiry = datetime.now(TZ) + timedelta(days=days)
                expiry_str = expiry.strftime("%d %B %Y, %I:%M %p")
                text = script.PREMIUM_ADDED.format(
                    name=target_name, id=user_id, username=target_username,
                    days=days, left=days, expiry=expiry_str,
                    admin_name=admin_name, admin_id=cq.from_user.id, admin_username=admin_username,
                    time=now
                )
                await client.send_message(LOG_CHANNEL, text)

        elif action == "confirm_remove":
            await db.remove_premium(user_id)
            await cq.message.edit_text(f"🚫 Premium removed from {user_id}.")
            await cq.answer("Premium removed!")

            text = script.PREMIUM_REMOVED.format(
                name=target_name, id=user_id, username=target_username,
                left=0, expiry="Expired",
                admin_name=admin_name, admin_id=cq.from_user.id, admin_username=admin_username,
                time=now
            )
            await client.send_message(LOG_CHANNEL, text)

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
        await message.reply(script.CHECK_ACTIVE.format(id=user_id, days=days, expiry=expiry_str))
    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium")],
             [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]
        )
        await message.reply(script.CHECK_INACTIVE, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^check_premium_user$"))
async def check_premium_btn(client: Client, cq: CallbackQuery):
    user_id = cq.from_user.id
    if await db.is_premium(user_id):
        days = await db.get_premium_days_left(user_id) or 0
        expiry = datetime.now(TZ) + timedelta(days=int(days))
        expiry_str = expiry.strftime("%d %B %Y, %I:%M %p")
        await cq.message.reply(script.CHECK_ACTIVE.format(id=user_id, days=days, expiry=expiry_str))
    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium")],
             [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]
        )
        await cq.message.reply(script.CHECK_INACTIVE, reply_markup=keyboard)


# ------------------------------
# Buy Premium
# ------------------------------
@Client.on_callback_query(filters.regex(r"^buy_premium$"))
async def buy_premium(client: Client, cq: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("👨‍💻 Contact Admin", url="https://t.me/YourAdminUsername")],
         [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]
    )
    await cq.message.reply(script.BUY_PREMIUM, reply_markup=keyboard)


