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

        # already premium? offer choices
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

        # not premium → create fresh premium with given days
        await db.add_premium(user_id, input_days)
        await message.reply(
            f"✅ Added premium to user `{user_id}` for {input_days} days.",
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


# 3) Remove Premium (Admin Only)
@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("⚠️ Usage: /removepremium user_id", quote=True)

        user_id = int(args[1])
        await db.remove_premium(user_id)
        await message.reply(f"🚫 Premium removed from user `{user_id}`.", quote=True)
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
@Client.on_callback_query(filters.regex(r"^(add_days|edit_days):\d+:\d+$"))
async def handle_premium_buttons(client: Client, cq: CallbackQuery):
    try:
        # only admins can press these buttons
        if cq.from_user.id not in ADMINS:
            await cq.answer("Not allowed.", show_alert=True)
            return

        action, user_id_str, new_days_str = cq.data.split(":")
        target_user_id = int(user_id_str)
        new_days = int(new_days_str)

        if new_days <= 0:
            await cq.answer("Days must be positive.", show_alert=True)
            return

        if action == "add_days":
            # add on top: total = left + new
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
            # overwrite with exactly new_days
            await db.add_premium(target_user_id, new_days)
            await cq.message.edit_text(
                f"✏️ Premium updated.\n"
                f"🆕 User `{target_user_id}` now has **{new_days} days** from today."
            )
            await cq.answer("Premium updated!")

    except Exception as e:
        try:
            await cq.answer("Something went wrong.", show_alert=True)
        except Exception:
            pass
        await cq.message.edit_text(f"❌ Error: {str(e)}")
        
