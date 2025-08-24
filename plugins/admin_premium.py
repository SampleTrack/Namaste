from pyrogram import Client, filters
from pyrogram.types import Message
from info import ADMINS
from database.users_chats_db import db

# 1) Add Premium (Admin Only)
@Client.on_message(filters.command("addpremium") & filters.user(ADMINS))
async def add_premium(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return await message.reply("⚠️ Usage: /addpremium user_id days")

        user_id = int(args[1])
        days = int(args[2])

        await db.add_premium(user_id, days)
        await message.reply(f"✅ Added premium to user `{user_id}` for {days} days.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")


# 2) Check Premium (User Command)
@Client.on_message(filters.command("checkpremium"))
async def check_premium(client: Client, message: Message):
    user_id = message.from_user.id
    if await db.is_premium(user_id):
        days = await db.get_premium_days_left(user_id)
        await message.reply(f"✨ You are a premium user!\n⏳ Days left: {days}")
    else:
        await message.reply("😢 You are not a premium user.")


# 3) Remove Premium (Admin Only)
@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("⚠️ Usage: /removepremium user_id")

        user_id = int(args[1])
        await db.remove_premium(user_id)
        await message.reply(f"🚫 Premium removed from user `{user_id}`.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")


# 4) Total Premium Users (Admin Only)
@Client.on_message(filters.command("totalpremium") & filters.user(ADMINS))
async def total_premium(client: Client, message: Message):
    total = await db.total_premium_users_count()
    await message.reply(f"📊 Total premium users: **{total}**")


# 5) Total Active Premium Users (Admin Only)
@Client.on_message(filters.command("activepremium") & filters.user(ADMINS))
async def active_premium(client: Client, message: Message):
    active = await db.total_active_premium_users_count()
    await message.reply(f"🔥 Active premium users: **{active}**")
    
