import os
import re
import json
import base64
import logging
import random
import asyncio
from datetime import datetime, timedelta, date, time
import pytz

from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.connections_mdb import active_connection

from Script import script
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from info import (
    PICS,
    ADMINS,
    CHANNELS, 
    LOG_CHANNEL,
    SUPPORT_CHAT,
    AUTH_CHANNEL, 
    UPDATE_CHANNEL, 
    BATCH_FILE_CAPTION, 
    CUSTOM_FILE_CAPTION, 
    PROTECT_CONTENT
)

logger = logging.getLogger(__name__)

BATCH_FILES = {}
RESULTS_PER_PAGE = 10


@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[           
            InlineKeyboardButton('📢 Uᴩᴅᴀᴛᴇꜱ 📢', url=SUPPORT_CHAT)
            ],[
            InlineKeyboardButton('ℹ️ Hᴇʟᴩ ℹ️', url=f"https://t.me/{temp.U_NAME}?start=help")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        mention = message.from_user.mention if message.from_user else message.chat.title
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await asyncio.sleep(2)
        if not await db.get_chat(message.chat.id):
            tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(tz)
            time = now.strftime('%I:%M:%S %p')
            today = now.date()
            total_members = await client.get_chat_members_count(message.chat.id)
            total_chats = await db.total_chat_count() + 1
            daily_chats = await db.daily_chats_count(today) + 1
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(a=message.chat.title, b=message.chat.id, c=message.chat.username, d=total_members, e=total_chats, f=daily_chats, g=str(today), h=time, i="Unknown", j=temp.B_NAME, k=temp.U_NAME))
            await db.add_chat(message.chat.id, message.chat.title, message.chat.username)
        return

    if not await db.is_user_exist(message.from_user.id):
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz)
        today = now.date()
        time = now.strftime('%I:%M:%S %p')
        total_users = await db.total_users_count() + 1
        daily_users = await db.daily_users_count(today) + 1
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(a=message.from_user.id, b=message.from_user.mention, c=message.from_user.username, d=total_users, e=daily_users, f=str(today), g=time, h=temp.B_NAME, i=temp.U_NAME))
    if len(message.command) != 2:
        buttons = [
            [
                InlineKeyboardButton("➕️ Add Me to Your Chat ➕", url=f"http://t.me/{temp.U_NAME}?startgroup=true")
            ],
            [
                InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat=''), 
                InlineKeyboardButton("📢 Channel", url=UPDATE_CHANNEL)
            ],
            [      
                InlineKeyboardButton("ℹ️ Help", callback_data="help"),
                InlineKeyboardButton("📚 About", callback_data="about")
            ]
        ]
        m = await message.reply_sticker("CAACAgUAAxkBAAEBvlVk7YKnYxIHVnKW2PUwoibIR2ygGAACBAADwSQxMYnlHW4Ls8gQHgQ") 
        await asyncio.sleep(2)
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return await m.delete()
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("MAKE SURE BOT IS ADMIN IN FORCESUB CHANNEL")
            return
        btn = [
            [   
                InlineKeyboardButton("Jᴏɪɴ Mʏ Cʜᴀɴɴᴇʟ ✨", url="https://t.me/addlist/HbZqccej2BQ2MmY9"),
            ],
            [
                InlineKeyboardButton("Jᴏɪɴ Mʏ Cʜᴀɴɴᴇʟ ✨", url=invite_link.invite_link)
            ]
        ]
        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton("⟳ Tʀʏ Aɢᴀɪɴ", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton("⟳ Tʀʏ Aɢᴀɪɴ", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
                
        try:
            return await client.send_message(chat_id=message.from_user.id, text=FORCE_SUB_TEXT, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.DEFAULT)
        except Exception as e:
            print(f"Force Sub Text Error\n{e}")
            return await client.send_message(chat_id=message.from_user.id, text=script.FORCE_SUB_TEXT, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.DEFAULT)
        
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [
            [
                InlineKeyboardButton("➕️ Add Me to Your Chat ➕", url=f"http://t.me/{temp.U_NAME}?startgroup=true")
            ],
            [
                InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat=''), 
                InlineKeyboardButton("📢 Channel", url=UPDATE_CHANNEL)
            ],
            [      
                InlineKeyboardButton("ℹ️ Help", callback_data="help"),
                InlineKeyboardButton("📚 About", callback_data="about")
            ]
        ]
        m = await message.reply_sticker("CAACAgUAAxkBAAEBvlVk7YKnYxIHVnKW2PUwoibIR2ygGAACBAADwSQxMYnlHW4Ls8gQHgQ") 
        await asyncio.sleep(2)
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return await m.delete()
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
        
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("PLEASE WAIT......")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(mention=message.from_user.mention, file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(chat_id=message.from_user.id, file_id=msg.get("file_id"), caption=f_caption, protect_content=msg.get('protect', False))
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.send_cached_media(chat_id=message.from_user.id, file_id=msg.get("file_id"), caption=f_caption, protect_content=msg.get('protect', False))
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        return await sts.delete()
        
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("PLEASE WAIT....")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("utf-8")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(mention=message.from_user.mention, file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1) 
        return await sts.delete()
        
    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("utf-8")).split("_", 1)
        try:
            msg = await client.send_cached_media(chat_id=message.from_user.id, file_id=file_id, protect_content=True if pre == 'filep' else False,)
            filetype = msg.media
            file = getattr(msg, filetype)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try: f_caption=CUSTOM_FILE_CAPTION.format(mention=message.from_user.mention, file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except: return
            return await msg.edit_caption(f_caption)
        except: pass
        return await message.reply('NO SUCH FILE EXIST...')
        
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(mention=message.from_user.mention, file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"
    await client.send_cached_media(
        chat_id=message.from_user.id, 
        file_id=file_id, 
        caption=f_caption, 
        protect_content=True if pre == 'filep' else False,
    )
    
    
@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    try:
        if isinstance(CHANNELS, (int, str)):
            channels = [CHANNELS]
        elif isinstance(CHANNELS, list):
            channels = CHANNELS
        else:
            raise ValueError("Unexpected type of CHANNELS")

        if not channels:
            await message.reply("No channels or groups found in CHANNELS variable.")
            return

        text = '📑 **Indexed channels/groups**\n'
        for channel in channels:
            chat = await bot.get_chat(channel)
            text += f'\n👥 **Title:** {chat.title or chat.first_name}'
            text += f'\n🆔 **ID:** {chat.id}'
            
            if chat.username:
                text += f'\n🌐 **Username:** @{chat.username}\n'
            else:
                invite_link = await bot.export_chat_invite_link(chat.id)
                text += f'\n🔗 **Invite:** {invite_link}\n'
                
        text += f'**Total:** {len(channels)}'

        if len(text) < 4096:
            await message.reply(text, disable_web_page_preview=True)
        else:
            file = 'Indexed_channels.txt'
            with open(file, 'w') as f:
                f.write(text)
            await message.reply_document(file, disable_web_page_preview=True)
            os.remove(file)
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
        
        
@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('Logs.txt')
    except Exception as e:
        await message.reply(str(e))
        
@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    reply = message.reply_to_message
    if reply and reply.media: msg = await message.reply("Processing...⏳", quote=True)
    else: return await message.reply('Reply to file with /delete which you want to delete', quote=True)
    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None: break
    else: return await msg.edit('This Is Not Supported File Format')
    file_id, file_ref = unpack_new_file_id(media.file_id)
    result = await Media.collection.delete_one({'_id': file_id})
    if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
        else:
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
            else: await msg.edit('File Not Found In Database')
            
            
@Client.on_message(filters.command(['findfiles']) & filters.user(ADMINS))
async def handle_find_files(client, message):
    """Find files in the database based on search criteria"""
    search_query = " ".join(message.command[1:])  # Extract the search query from the command

    if not search_query:
        return await message.reply('✨ Please provide a name.\n\nExample: /findfiles Kantara.', quote=True)

    # Build the MongoDB query to search for files
    query = {
        'file_name': {"$regex": f".*{re.escape(search_query)}.*", "$options": "i"}
    }

    # Fetch the matching files from the database
    results = await Media.collection.find(query).to_list(length=None)

    if len(results) > 0:
        confirmation_message = f'✨ {len(results)} files found matching the search query "{search_query}" in the database:\n\n'
        starting_query = {
            'file_name': {"$regex": f"^{re.escape(search_query)}", "$options": "i"}
        }
        starting_results = await Media.collection.find(starting_query).to_list(length=None)
        confirmation_message += f'✨ {len(starting_results)} files found starting with "{search_query}" in the database.\n\n'
        confirmation_message += '✨ Please select the option for easier searching:'

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🌟 Find Related", callback_data=f"related_files:1:{search_query}"),
                    InlineKeyboardButton("🌟 Find Starting", callback_data=f"starting_files:1:{search_query}")
                ],
                [
                    InlineKeyboardButton("🗑️ Delete Related", callback_data=f"confirm_delete_related:{search_query}"),
                    InlineKeyboardButton("🗑️ Delete Starting", callback_data=f"confirm_delete_starting:{search_query}")
                ],
                [
                    InlineKeyboardButton("❌ Cancel", callback_data="manage:cancel")
                ]
            ]
        )
        await message.reply_text(confirmation_message, reply_markup=keyboard)
    else:
        await message.reply('❌ No files found matching the search query.', quote=True)
        
        
@Client.on_callback_query(filters.regex('^related_files'))
async def find_related_files(client, callback_query):
    data = callback_query.data.split(":")
    page = int(data[1])
    search_query = data[2]
    query = {
        'file_name': {"$regex": f".*{re.escape(search_query)}.*", "$options": "i"}
    }
    results = await Media.collection.find(query).to_list(length=None)

    total_results = len(results)
    num_pages = total_results // RESULTS_PER_PAGE + 1

    start_index = (page - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE
    current_results = results[start_index:end_index]

    result_message = f'{len(current_results)} files found with related names to "{search_query}" in the database:\n\n'
    for result in current_results:
        result_message += f'File Name: {result["file_name"]}\n'
        result_message += f'File Size: {result["file_size"]}\n\n'

    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"related_files:{page-1}:{search_query}"))

    if page < num_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"related_files:{page+1}:{search_query}"))

    buttons.append(InlineKeyboardButton("🔚 Cancel", callback_data="cancel_find"))

    # Create button groups with two buttons each
    button_groups = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    keyboard = InlineKeyboardMarkup(button_groups)

    await callback_query.message.edit_text(result_message, reply_markup=keyboard)
    await callback_query.answer()
    
    
@Client.on_callback_query(filters.regex('^starting_files'))
async def find_starting_files(client, callback_query):
    data = callback_query.data.split(":")
    page = int(data[1])
    search_query = data[2]
    query = {
        'file_name': {"$regex": f"^{re.escape(search_query)}", "$options": "i"}
    }
    results = await Media.collection.find(query).to_list(length=None)

    total_results = len(results)
    num_pages = total_results // RESULTS_PER_PAGE + 1

    start_index = (page - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE
    current_results = results[start_index:end_index]

    result_message = f'{len(current_results)} files found with names starting "{search_query}" in the database:\n\n'
    for result in current_results:
        result_message += f'File Name: {result["file_name"]}\n'
        result_message += f'File Size: {result["file_size"]}\n\n'

    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"related_files:{page-1}:{search_query}"))

    if page < num_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"related_files:{page+1}:{search_query}"))

    buttons.append(InlineKeyboardButton("🔚 Cancel", callback_data=f"cancel_find"))

    # Create button groups with two buttons each
    button_groups = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    keyboard = InlineKeyboardMarkup(button_groups)

    await callback_query.message.edit_text(result_message, reply_markup=keyboard)
    await callback_query.answer()
    
    
@Client.on_callback_query(filters.regex('^delete_related'))
async def delete_related_files(client, callback_query):
    file_name = callback_query.data.split(":", 1)[1]
    result = await Media.collection.delete_many({
        'file_name': {"$regex": f".*{re.escape(file_name)}.*", "$options": "i"}
    })

    if result.deleted_count:
        message_text = f"✅ Deleted {result.deleted_count} files."
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletename"),
                    InlineKeyboardButton("⬅️ Back", callback_data=f"confirm_delete_related:{file_name}")
                ],
                [
                    InlineKeyboardButton("🔚 Cancel", callback_data="cancel_delete")
                ]
            ]
        )
    else:
        message_text = "❌ Deletion failed. No files deleted."
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletename"),
                    InlineKeyboardButton("⬅️ Back", callback_data=f"confirm_delete_related:{file_name}")
                ],
                [
                    InlineKeyboardButton("🔚 Cancel", callback_data="cancel_delete")
                ]
            ]
        )

    await callback_query.message.edit_text(message_text, reply_markup=keyboard)
    
    
@Client.on_callback_query(filters.regex('^confirm_delete_related'))
async def confirm_delete_related_files(client, callback_query):
    file_name = callback_query.data.split(":", 1)[1]
    confirmation_message = f'⚠️ Are you sure you want to delete all files with the name "{file_name}"?\n\n' \
                           f'This action cannot be undone.'

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"delete_related:{file_name}"),
                InlineKeyboardButton("🏠 Home", callback_data="deletename")
            ],
            [
                InlineKeyboardButton("🔚 Cancel", callback_data="cancel_delete")
            ]
        ]
    )

    await callback_query.message.edit_text(confirmation_message, reply_markup=keyboard)
    
    
@Client.on_callback_query(filters.regex('^delete_starting'))
async def delete_starting_files(client, callback_query):
    file_name = callback_query.data.split(":", 1)[1]
    result = await Media.collection.delete_many({
        'file_name': {"$regex": f"^{re.escape(file_name)}", "$options": "i"}
    })

    if result.deleted_count:
        message_text = f"✅ Deleted {result.deleted_count} files."
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletename"),
                    InlineKeyboardButton("⬅️ Back", callback_data=f"confirm_delete_starting:{file_name}")
                ],
                [
                    InlineKeyboardButton("🔚 Cancel", callback_data="cancel_delete")
                ]
            ]
        )
    else:
        message_text = "❌ Deletion failed. No files deleted."
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletename"),
                    InlineKeyboardButton("⬅️ Back", callback_data=f"confirm_delete_starting:{file_name}")
                ],
                [
                    InlineKeyboardButton("🔚 Cancel", callback_data="cancel_delete")
                ]
            ]
        )

    await callback_query.message.edit_text(message_text, reply_markup=keyboard)
    
    
@Client.on_callback_query(filters.regex('^confirm_delete_starting'))
async def confirm_delete_starting_files(client, callback_query):
    file_name = callback_query.data.split(":", 1)[1]
    confirmation_message = f'⚠️ Are you sure you want to delete all files with names starting "{file_name}"?\n\n' \
                           f'This action cannot be undone.'

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"delete_starting:{file_name}"),
                InlineKeyboardButton("🏠 Home", callback_data="deletename")
            ],
            [
                InlineKeyboardButton("🔚 Cancel", callback_data="cancel_delete")
            ]
        ]
    )

    await callback_query.message.edit_text(confirmation_message, reply_markup=keyboard)
    
    
@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'Tʜɪs ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ғɪʟᴇs.\nDᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ?',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Yᴇs", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Cᴀɴᴄᴇʟ", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )
    
    
@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await Media2.collection.drop()
    await message.answer("Eᴠᴇʀʏᴛʜɪɴɢ's Gᴏɴᴇ")
    await message.message.edit('Sᴜᴄᴄᴇsғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ Aʟʟ Tʜᴇ Iɴᴅᴇxᴇᴅ Fɪʟᴇs.')
    
    
@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid: return await message.reply(f"Yᴏᴜ Aʀᴇ Aɴᴏɴʏᴍᴏᴜs Aᴅᴍɪɴ. Usᴇ /connect {message.chat.id} Iɴ PM")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                return await message.reply_text("Mᴀᴋᴇ Sᴜʀᴇ I'ᴍ Pʀᴇsᴇɴᴛ Iɴ Yᴏᴜʀ Gʀᴏᴜᴘ!!", quote=True)
        else: return await message.reply_text("I'ᴍ Nᴏᴛ Cᴏɴɴᴇᴄᴛᴇᴅ Tᴏ Aɴʏ Gʀᴏᴜᴘs!", quote=True)

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title
    else: return

    st = await client.get_chat_member(grp_id, userid)
    if (
        st.status != enums.ChatMemberStatus.ADMINISTRATOR
        and st.status != enums.ChatMemberStatus.OWNER
        and str(userid) not in ADMINS
    ): return

    settings = await get_settings(grp_id)
    if settings is not None:
        buttons = [[
            InlineKeyboardButton(f"ꜰɪʟᴛᴇʀ ʙᴜᴛᴛᴏɴ : {'sɪɴɢʟᴇ' if settings['button'] else 'ᴅᴏᴜʙʟᴇ'}", f'setgs#button#{settings["button"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ꜰɪʟᴇ ɪɴ ᴩᴍ ꜱᴛᴀʀᴛ: {'ᴏɴ' if settings['botpm'] else 'ᴏꜰꜰ'}", f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
            ],[                
            InlineKeyboardButton(f"ʀᴇꜱᴛʀɪᴄᴛ ᴄᴏɴᴛᴇɴᴛ : {'ᴏɴ' if settings['file_secure'] else 'ᴏꜰꜰ'}", f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ɪᴍᴅʙ ɪɴ ꜰɪʟᴛᴇʀ : {'ᴏɴ' if settings['imdb'] else 'ᴏꜰꜰ'}", f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ꜱᴩᴇʟʟɪɴɢ ᴄʜᴇᴄᴋ : {'ᴏɴ' if settings['spell_check'] else 'ᴏꜰꜰ'}", f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇ : {'ᴏɴ' if settings['welcome'] else 'ᴏꜰꜰ'}", f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
        ]]
        await message.reply_text(
            text=f"<b>Cʜᴀɴɢᴇ Yᴏᴜʀ Sᴇᴛᴛɪɴɢꜱ Fᴏʀ {title} Aꜱ Yᴏᴜʀ Wɪꜱʜ ⚙</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True, 
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
        )
        
        
@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("Cʜᴇᴄᴋɪɴɢ Tᴇᴍᴘʟᴀᴛᴇ")
    userid = message.from_user.id if message.from_user else None
    if not userid: return await message.reply(f"Yᴏᴜ Aʀᴇ Aɴᴏɴʏᴍᴏᴜs Aᴅᴍɪɴ. Usᴇ /connect {message.chat.id} Iɴ PM")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                return await message.reply_text("Mᴀᴋᴇ Sᴜʀᴇ I'ᴍ Pʀᴇsᴇɴᴛ Iɴ Yᴏᴜʀ Gʀᴏᴜᴘ !!", quote=True)
        else:
            return await message.reply_text("I'ᴍ Nᴏᴛ Cᴏɴɴᴇᴄᴛᴇᴅ Tᴏ Aɴʏ Gʀᴏᴜᴘs!", quote=True)
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title
    else: return
    st = await client.get_chat_member(grp_id, userid)
    if (
        st.status != enums.ChatMemberStatus.ADMINISTRATOR
        and st.status != enums.ChatMemberStatus.OWNER
        and str(userid) not in ADMINS
    ): return
    if len(message.command) < 2: return await sts.edit("No Iɴᴩᴜᴛ!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"Sᴜᴄᴄᴇssғᴜʟʟʏ Cʜᴀɴɢᴇᴅ Tᴇᴍᴘʟᴀᴛᴇ Fᴏʀ {title} Tᴏ\n\n{template}")
    
    
@Client.on_message(filters.command('get_template'))
async def geg_template(client, message):
    sts = await message.reply("Cʜᴇᴄᴋɪɴɢ Tᴇᴍᴘʟᴀᴛᴇ")
    userid = message.from_user.id if message.from_user else None
    if not userid: return await message.reply(f"Yᴏᴜ Aʀᴇ Aɴᴏɴʏᴍᴏᴜs Aᴅᴍɪɴ. Usᴇ /connect {message.chat.id} Iɴ PM")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                return await message.reply_text("Mᴀᴋᴇ Sᴜʀᴇ I'ᴍ Pʀᴇsᴇɴᴛ Iɴ Yᴏᴜʀ Gʀᴏᴜᴘ !!", quote=True)
        else:
            return await message.reply_text("I'ᴍ Nᴏᴛ Cᴏɴɴᴇᴄᴛᴇᴅ Tᴏ Aɴʏ Gʀᴏᴜᴘs!", quote=True)
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title
    else: return
    st = await client.get_chat_member(grp_id, userid)
    if (
        st.status != enums.ChatMemberStatus.ADMINISTRATOR
        and st.status != enums.ChatMemberStatus.OWNER
        and str(userid) not in ADMINS
    ): return
    settings = await get_settings(grp_id)
    template = settings['template']
    await sts.edit(f"Cᴜʀʀᴇɴᴛ Tᴇᴍᴘʟᴀᴛᴇ Fᴏʀ {title} Iꜱ\n\n{template}")
    
