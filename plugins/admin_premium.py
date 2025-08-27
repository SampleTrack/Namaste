from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from info import ADMINS
from database.users_chats_db import db


# 1) Add Premium (Admin Only)
@Client.on_message(filters.command("addpremium") & filters.user(ADMINS))
async def add_premium(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return await message.reply("⚠️ Usage: /addpremium user_id days", quote=True)

        user_id = int(args[1])
        input_days = int(args[2])
        if input_days <= 0:
            return await message.reply("⚠️ Days must be a positive number.", quote=True)

        # already premium? → offer choices
        if await db.is_premium(user_id):
            days_left = await db.get_premium_days_left(user_id)
            days_left = int(days_left or 0)

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➕ Add More Days",
                            callback_data=f"add_days:{user_id}:{input_days}"
                        ),
                        InlineKeyboardButton(
                            "✏️ Edit Premium Days",
                            callback_data=f"edit_days:{user_id}:{input_days}"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Cancel",
                            callback_data="cancel_action"
                        )
                    ]
                ]
            )
            return await message.reply(
                (
                    f"⚠️ User `{user_id}` is already premium.\n"
                    f"⏳ Current days left: **{days_left}**\n\n"
                    f"Choose an action:"
                ),
                reply_markup=keyboard,
                quote=True,
            )

        # not premium → confirm first
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Confirm Add Premium",
                        callback_data=f"confirm_add:{user_id}:{input_days}"
                    ),
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="cancel_action"
                    )
                ]
            ]
        )
        await message.reply(
            f"🤔 User `{user_id}` is **not premium**.\n"
            f"Do you want to add premium for **{input_days} days**?",
            reply_markup=keyboard,
            quote=True,
        )

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}", quote=True)


# 2) Check Premium (User Command)
@Client.on_message(filters.command("checkpremium"))
async def check_premium(client: Client, message: Message):
    user_id = message.from_user.id
    if await db.is_premium(user_id):
        days = await db.get_premium_days_left(user_id)
        await message.reply(f"✨ You are a premium user!\n⏳ Days left: {days}", quote=True)
    else:
        await message.reply("😢 You are not a premium user.", quote=True)


# 3) Remove Premium (Admin Only, now with confirm)
@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("⚠️ Usage: /removepremium user_id", quote=True)

        user_id = int(args[1])

        # confirm buttons
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Confirm Remove",
                        callback_data=f"confirm_remove:{user_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="cancel_action"
                    )
                ]
            ]
        )
        await message.reply(
            f"⚠️ Are you sure you want to remove premium from user `{user_id}`?",
            reply_markup=keyboard,
            quote=True,
        )

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}", quote=True)


# 4) Total Premium Users (Admin Only)
@Client.on_message(filters.command("totalpremium") & filters.user(ADMINS))
async def total_premium(client: Client, message: Message):
    total = await db.total_premium_users_count()
    await message.reply(f"📊 Total premium users: **{total}**", quote=True)


# 5) Total Active Premium Users (Admin Only)
@Client.on_message(filters.command("activepremium") & filters.user(ADMINS))
async def active_premium(client: Client, message: Message):
    active = await db.total_active_premium_users_count()
    await message.reply(f"🔥 Active premium users: **{active}**", quote=True)


# 🔔 Inline button callbacks (admins only)
@Client.on_callback_query(filters.regex(r"^(add_days|edit_days|confirm_add|confirm_remove|cancel_action):"))
async def handle_premium_buttons(client: Client, cq: CallbackQuery):
    try:
        if cq.from_user.id not in ADMINS:
            await cq.answer("Not allowed.", show_alert=True)
            return

        data = cq.data.split(":")
        action = data[0]

        if action in ["add_days", "edit_days", "confirm_add"]:
            target_user_id = int(data[1])
            new_days = int(data[2])

            if new_days <= 0:
                await cq.answer("Days must be positive.", show_alert=True)
                return

            if action == "add_days":
                left = await db.get_premium_days_left(target_user_id)
                left = int(left or 0)
                total_days = left + new_days
                await db.add_premium(target_user_id, total_days)
                await cq.message.edit_text(
                    f"✅ Added **{new_days} days** on top.\n"
                    f"🆕 Premium for user `{target_user_id}` is now **{total_days} days** from today."
                )
                await cq.answer("Premium extended!")

            elif action == "edit_days":
                await db.add_premium(target_user_id, new_days)
                await cq.message.edit_text(
                    f"✏️ Premium updated.\n"
                    f"🆕 User `{target_user_id}` now has **{new_days} days** from today."
                )
                await cq.answer("Premium updated!")

            elif action == "confirm_add":
                await db.add_premium(target_user_id, new_days)
                await cq.message.edit_text(
                    f"✅ Premium activated!\n"
                    f"🆕 User `{target_user_id}` now has **{new_days} days** from today."
                )
                await cq.answer("Premium added!")

        elif action == "confirm_remove":
            target_user_id = int(data[1])
            await db.remove_premium(target_user_id)
            await cq.message.edit_text(
                f"🚫 Premium removed from user `{target_user_id}`."
            )
            await cq.answer("Premium removed!")

        elif action == "cancel_action":
            await cq.message.edit_text("❌ Action cancelled.")
            await cq.answer("Cancelled!")

    except Exception as e:
        try:
            await cq.answer("Something went wrong.", show_alert=True)
        except Exception:
            pass
        await cq.message.edit_text(f"❌ Error: {str(e)}")
        
