from pyrogram import Client, filters
from pyrogram.types import *
from aiohttp import ClientSession
from telegraph import upload_file, TelegraphException # Import TelegraphException
from io import BytesIO

ai_client = ClientSession()

async def make_carbon(code, tele=False):
    url = "https://carbonara.solopov.dev/api/cook"
    async with ai_client.post(url, json={"code": code}) as resp:
        image = BytesIO(await resp.read())
    image.name = "carbon.png"
    if tele:
        try:
            uf = upload_file(image)
            image.close()
            # Check if uf is a list as expected and has at least one element
            if isinstance(uf, list) and len(uf) > 0:
                return f"https://graph.org{uf[0]}"
            else:
                # Handle cases where uf is not as expected, perhaps a non-list or empty
                print(f"Telegraph upload_file did not return a list as expected: {uf}")
                return None # Or raise a custom exception, or return a default
        except TelegraphException as e:
            print(f"Telegraph API error during upload: {e}")
            return None # Or raise a custom exception, or return a default
        except AttributeError as e:
            # This specific error (AttributeError: 'str' object has no attribute 'get')
            # is what you observed, but it originates from within the telegraph library.
            # Catching it here allows you to log/handle it.
            print(f"AttributeError during Telegraph upload: {e}. Raw response might have been a string.")
            return None
        except Exception as e:
            # Catch any other unexpected errors during the upload process
            print(f"An unexpected error occurred during Telegraph upload: {e}")
            return None
    return image


@Client.on_message(filters.command("carbon"))
async def carbon_func(b, message):
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇxᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴀᴋᴇ ᴄᴀʀʙᴏɴ.")
    if not message.reply_to_message.text:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇxᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴀᴋᴇ ᴄᴀʀʙᴏɴ.")
    user_id = message.from_user.id
    m = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ...")
    carbon = await make_carbon(message.reply_to_message.text)

    if carbon: # Check if make_carbon returned a valid image or URL
        await m.edit("ᴜᴘʟᴏᴀᴅɪɴɢ..")
        if isinstance(carbon, str): # It's a Telegraph URL
            await message.reply_text(
                text=f"**ᴍᴀᴅᴇ ʙʏ: @mkn_bots_updates**\n\n[Carbon Image]({carbon})", # Provide the link
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ꜱᴜᴩᴩᴏʀᴛ ᴜꜱ", url="https://t.me/mkn_bots_updates")]])
            )
        else: # It's a BytesIO object for direct photo upload
            await message.reply_photo(
                photo=carbon,
                caption="**ᴍᴀᴅᴇ ʙʏ: @mkn_bots_updates**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ꜱᴜᴩᴩᴏʀᴛ ᴜꜱ", url="https://t.me/mkn_bots_updates")]])
            )
        await m.delete()
        if not isinstance(carbon, str): # Close only if it's a BytesIO object
            carbon.close()
    else:
        await m.edit("ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴏʀ ᴜᴘʟᴏᴀᴅ ᴄᴀʀʙᴏɴ ɪᴍᴀɢᴇ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
        await m.delete()

