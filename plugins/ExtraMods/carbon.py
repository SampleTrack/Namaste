from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import ClientSession
from telegraph import upload_file
from io import BytesIO
import tempfile
import os

ai_client = ClientSession()

async def make_carbon(code, tele=False):
    url = "https://carbonara.solopov.dev/api/cook"
    async with ai_client.post(url, json={"code": code}) as resp:
        image = BytesIO(await resp.read())
    image.name = "carbon.png"
    if tele:
        # Save image to a temp file and upload using file path
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(image.getbuffer())
            temp_path = f.name
        uf = upload_file(temp_path)
        image.close()
        os.unlink(temp_path)  # Cleanup the temp file
        return f"<https://graph.org{uf>[0]}"
    return image

@Client.on_message(filters.command("carbon"))
async def carbon_func(b, message):
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇxᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴀᴋᴇ ᴄᴀʀʙᴏɴ.")
    if not message.reply_to_message.text:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇxᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴀᴋᴇ ᴄᴀʀʙᴏɴ.")
    m = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ...")
    carbon = await make_carbon(message.reply_to_message.text)
    await m.edit("ᴜᴘʟᴏᴀᴅɪɴɢ..")
    await message.reply_photo(
        photo=carbon,
        caption="**ᴍᴀᴅᴇ ʙʏ: @mkn_bots_updates**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ꜱᴜᴩᴩᴏʀᴛ ᴜꜱ", url="https://t.me/mkn_bots_updates")]
        ]),
    )
    await m.delete()
    carbon.close()
