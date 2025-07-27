from pyrogram import Client, filters, enums
from pyrogram.types import *
from aiohttp import ClientSession
from io import BytesIO
import psutil, shutil, time
from utils import get_time, humanbytes  # make sure you have these

ai_client = ClientSession()

async def make_carbon(code):
    url = "https://carbonara.solopov.dev/api/cook"
    async with ai_client.post(url, json={"code": code}) as resp:
        if resp.status == 200:
            image = BytesIO(await resp.read())
            image.name = "carbon.png"
            return image
    return None
    
    
@Client.on_message(filters.command("carbon"))
async def carbon_func(b, message):
    if not message.reply_to_message or not message.reply_to_message.text:
        return await message.reply_text("📝 ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇxᴛ ᴍᴇssᴀɢᴇ.")

    m = await message.reply_text("🎨 Cʀᴇᴀᴛɪɴɢ Cᴀʀʙᴏɴ...")

    carbon_img = await make_carbon(message.reply_to_message.text)

    if not carbon_img:
        return await m.edit("❌ Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴄᴀʀʙᴏɴ.")

    await m.edit("⏫ Uᴘʟᴏᴀᴅɪɴɢ...")

    await message.reply_photo(
        photo=carbon_img,
        caption="✨ Mᴀᴅᴇ Bʏ: @mkn_bots_updates",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💖 Sᴜᴘᴘᴏʀᴛ Uꜱ", url="https://t.me/mkn_bots_updates")]
        ])
    )

    await m.delete()
    carbon_img.close()
