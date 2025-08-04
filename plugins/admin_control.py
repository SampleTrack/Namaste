from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid, UserNotParticipant, MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from info import ADMINS, LOG_CHANNEL, SUPPORT_CHAT, UPDATE_CHANNEL, IMDB_TEMPLATE, UPTIME 
from utils import get_size, temp, extract_user, get_file_id, get_poster, humanbytes, get_settings
from database.users_chats_db import db
from database.ia_filterdb import Media
from datetime import datetime, timedelta
import asyncio 
from datetime import date, datetime, timedelta
import pytz
from Script import script
import logging, re, asyncio, time, shutil, psutil, io, os, sys
from pyrogram import Client, filters
from info import ADMINS


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


# Configurations
USE_12_HOUR_FORMAT = True             # Switch 12/24 hour format ON/OFF here


def extract_commands_from_file(file_path):
    commands = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if "filters.command" in line:
                cmd_match = re.search(r"filters\.command\((.*?)\)", line)
                if cmd_match:
                    raw_cmds = cmd_match.group(1)
                    try:
                        # Convert string like "['filter', 'add']" to actual list
                        cmd_list = eval(raw_cmds, {"__builtins__": {}})
                    except:
                        cmd_list = [raw_cmds.strip("'\"")]
                    if not isinstance(cmd_list, list):
                        cmd_list = [cmd_list]

                    is_admin = "filters.user(ADMINS)" in line or "filters.user(ADMINS)" in line.replace(" ", "")
                    commands.append((cmd_list, is_admin))
    return commands


def list_commands_in_project(directory):
    all_commands = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                commands = extract_commands_from_file(file_path)
                if commands:
                    all_commands[file_path] = commands
    return all_commands


@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    new_members = [member.id for member in message.new_chat_members]
    if temp.ME in new_members:
        if not await db.get_chat(message.chat.id):
            tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(tz)
            time = now.strftime('%I:%M:%S %p')
            today = now.date()
            total_members = await bot.get_chat_members_count(message.chat.id)
            total_chats = await db.total_chat_count() + 1
            daily_chats = await db.daily_chats_count(today) + 1
            referrer = message.from_user.mention if message.from_user else "Anonymous"
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(a=message.chat.title, b=message.chat.id, c=message.chat.username, d=total_members, e=total_chats, f=daily_chats, g=str(today), h=time, i=referrer, j=temp.U_NAME))
            await db.add_chat(message.chat.id, message.chat.title, message.chat.username)
            
        if message.chat.id in temp.BANNED_CHATS:
            buttons = [[
                InlineKeyboardButton('Support', url=SUPPORT_CHAT)
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            message_text = '<b>CHAT NOT ALLOWED 🐞\n\nMy admins have restricted me from working here! If you want to know more about it, contact support.</b>'
            sent_message = await message.reply(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
            try:
                await sent_message.pin()
            except Exception as e:
                print(e)

            await bot.leave_chat(message.chat.id)
            return
            
    else:
        settings = await get_settings(message.chat.id)
        invite_link = None  # Initialize invite_link to None
    
        # Generate or get the invite link for this chat
        chat_id = message.chat.id
        if invite_link is None:
            invite_link = await db.get_chat_invite_link(chat_id)
            if invite_link is None:
                try:
                    invite_link = await bot.export_chat_invite_link(chat_id)
                except ChatAdminRequired:
                    invite_link = "Not an Admin"
                    return
                await db.save_chat_invite_link(chat_id, invite_link)
    
        if settings["welcome"]:
            for member in new_members:
                if temp.MELCOW.get('welcome') is not None:
                    try:
                        await temp.MELCOW['welcome'].delete()
                    except Exception as e:
                        print(e)

                mention = message.from_user.mention if message.from_user else message.chat.title
                temp.MELCOW['welcome'] = await message.reply_photo(
                    photo=MELCOW_PIC,
                    caption=script.MELCOW_ENG.format(a=mention, b=message.chat.title),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('Support Group', url=SUPPORT_CHAT),
                                InlineKeyboardButton('Updates Channel', url=UPDATE_CHANNEL)
                            ]
                        ]
                    ),
                    parse_mode=enums.ParseMode.HTML
                )
    
                # Log new members joining the group
                tz = pytz.timezone('Asia/Kolkata')
                now = datetime.now(tz)
                time = now.strftime('%I:%M:%S %p')
                date = now.date()
                total_members = await bot.get_chat_members_count(message.chat.id)
    
                for member in new_members:
                    await bot.send_message(LOG_CHANNEL, script.NEW_MEMBER.format(a=message.chat.title, b=message.chat.id, c=message.chat.username, d=total_members, e=invite_link, f=message.from_user.mention, g=message.from_user.id, h=message.from_user.username, i=date, j=time, k=temp.U_NAME), disable_web_page_preview=True)
        else:
            # Log new members joining the group
            tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(tz)
            time = now.strftime('%I:%M:%S %p')
            date = now.date()
            total_members = await bot.get_chat_members_count(message.chat.id)
    
            for member in new_members:
                await bot.send_message(LOG_CHANNEL, script.NEW_MEMBER.format(a=message.chat.title, b=message.chat.id, c=message.chat.username, d=total_members, e=invite_link, f=message.from_user.mention, g=message.from_user.id, h=message.from_user.username, i=date, j=time, k=temp.U_NAME), disable_web_page_preview=True)
        
        if settings["auto_delete"]:
            await asyncio.sleep(600)
            await temp.MELCOW['welcome'].delete()
            
            
# Handler for logging members leaving the group
@Client.on_message(filters.left_chat_member & filters.group)
async def goodbye(bot, message):
    invite_link = None  # Initialize invite_link to None

    # Generate or get the invite link for this chat
    chat_id = message.chat.id
    if invite_link is None:
        invite_link = await db.get_chat_invite_link(chat_id)
        if invite_link is None:
            try:
                invite_link = await bot.export_chat_invite_link(chat_id)
            except ChannelPrivate:
                invite_link = "Not an Admin"
                return 
            except ChatAdminRequired:
                invite_link = "Not an Admin"
                return
            await db.save_chat_invite_link(chat_id, invite_link)
    
    # Get total members count
    try:
        total_members = await bot.get_chat_members_count(message.chat.id)
    except ChannelPrivate:
        total_members = "Not an Admin"
        return
    
    # Get current time and date
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    time = now.strftime('%I:%M:%S %p')
    date = now.date()
    
    # Check if chat exists in the database
    if await db.get_chat(message.chat.id):
        left_member = message.left_chat_member  # Get the left member info
        
        # Get bot's information
        bot_info = await bot.get_me()
        bot_id = bot_info.id
        
        if left_member.id == bot_id:  # Check if the left member is the bot itself
            await bot.send_message(LOG_CHANNEL, script.LEFT_MEMBER.format(a=message.chat.title, b=message.chat.id, c=message.chat.username, d=total_members, e=invite_link, f=left_member.mention, g=left_member.id, h=left_member.username, i=date, j=time, k=temp.U_NAME), disable_web_page_preview=True)
        else:
            await bot.send_message(LOG_CHANNEL, script.LEFT_MEMBER.format(a=message.chat.title, b=message.chat.id, c=message.chat.username, d=total_members, e=invite_link, f=left_member.mention, g=left_member.id, h=left_member.username, i=date, j=time, k=temp.U_NAME), disable_web_page_preview=True)


@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) == 1: return await message.reply('Gɪᴠᴇ Mᴇ A Cʜᴀᴛ Iᴅ')
    chat = message.command[1]
    try: chat = int(chat)
    except: chat = chat
    try:
        buttons = [[InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url=f'https://t.me/{SUPPORT_CHAT}')]]
        await bot.send_message(chat_id=chat, text='<b>Hᴇʟʟᴏ Fʀɪᴇɴᴅs, \nMʏ Aᴅᴍɪɴ Hᴀs Tᴏʟᴅ Mᴇ Tᴏ Lᴇᴀᴠᴇ Fʀᴏᴍ Gʀᴏᴜᴘ Sᴏ I Gᴏ! Iғ Yᴏᴜ Wᴀɴɴᴀ Aᴅᴅ Mᴇ Aɢᴀɪɴ Cᴏɴᴛᴀᴄᴛ Mʏ Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ</b>', reply_markup=InlineKeyboardMarkup(buttons))
        await bot.leave_chat(chat)
    except Exception as e:
        await message.reply(f'Eʀʀᴏʀ: {e}')

@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1: return await message.reply('Gɪᴠᴇ Mᴇ A Cʜᴀᴛ Iᴅ')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No Reason Provided"
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Gɪᴠᴇ Mᴇ A Vᴀʟɪᴅ Cʜᴀᴛ ID')
    cha_t = await db.get_chat(int(chat_))
    if not cha_t:
        return await message.reply("Cʜᴀᴛ Nᴏᴛ Fᴏᴜɴᴅ Iɴ DB")
    if cha_t['is_disabled']:
        return await message.reply(f"Tʜɪꜱ Cʜᴀᴛ Is Aʟʀᴇᴅʏ  Dɪꜱᴀʙʟᴇᴅ:\nRᴇᴀꜱᴏɴ: <code> {cha_t['reason']} </code>")
    await db.disable_chat(int(chat_), reason)
    temp.BANNED_CHATS.append(int(chat_))
    await message.reply('Cʜᴀᴛ Sᴜᴄᴄᴇꜱꜰᴜʟʟʏ Dɪꜱᴀʙʟᴇᴅ')
    try:
        buttons = [[InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url=f'https://t.me/{SUPPORT_CHAT}')]]
        await bot.send_message(chat_id=chat_,  text=f'<b>Hᴇʟʟᴏ Fʀɪᴇɴᴅs, \nᴍʏ Aᴅᴍɪɴ Hᴀs Tᴏʟᴅ Mᴇ Tᴏ Lᴇᴀᴠᴇ Fʀᴏᴍ Gʀᴏᴜᴘ Sᴏ I Gᴏ! Iғ Yᴏᴜ Wᴀɴɴᴀ Aᴅᴅ Mᴇ Aɢᴀɪɴ Cᴏɴᴛᴀᴄᴛ Mʏ Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ.</b> \nRᴇᴀꜱᴏɴ : <code>{reason}</code>', reply_markup=InlineKeyboardMarkup(buttons))
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"Eʀʀᴏʀ: {e}")


@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1: return await message.reply('Gɪᴠᴇ Mᴇ A Cʜᴀᴛ Iᴅ')
    chat = message.command[1]
    try: chat_ = int(chat)
    except: return await message.reply('Gɪᴠᴇ Mᴇ A Vᴀʟɪᴅ Cʜᴀᴛ ID')
    sts = await db.get_chat(int(chat))
    if not sts: return await message.reply("Cʜᴀᴛ Nᴏᴛ Fᴏᴜɴᴅ Iɴ DB")
    if not sts.get('is_disabled'):
        return await message.reply('Tʜɪꜱ Cʜᴀᴛ Iꜱ Nᴏᴛ Yᴇᴛ Dɪꜱᴀʙʟᴇᴅ')
    await db.re_enable_chat(int(chat_))
    temp.BANNED_CHATS.remove(int(chat_))
    await message.reply("Cʜᴀᴛ Sᴜᴄᴄᴇꜱꜰᴜʟʟʏ Rᴇ-Eɴᴀʙʟᴇᴅ")


@Client.on_message(filters.command('stats') & filters.incoming)
async def get_ststs(bot, message):
    rju = await message.reply('<b>Pʟᴇᴀꜱᴇ Wᴀɪᴛ...</b>')
    total_users = await db.total_users_count()
    totl_chats = await db.total_chat_count()
    files = await Media.count_documents()
    size = await db.get_db_size()
    free = 536870912 - size
    size = get_size(size)
    free = get_size(free)
    await rju.edit(script.STATUS_TXT.format(files, total_users, totl_chats, size, free))

@Client.on_message(filters.command("dbsize"))
async def db_size_handler(client, message):
    stats = db.command("dbstats")
    storage_size = stats.get("storageSize", 0)
    data_size = stats.get("dataSize", 0)
    total_size_mb = (storage_size + data_size) / (1024 * 1024)

    await message.reply_text(
        f"🗄️ Database Size:\n"
        f"- Data Size: {data_size / (1024 * 1024):.2f} MB\n"
        f"- Storage Size: {storage_size / (1024 * 1024):.2f} MB\n"
        f"- Total: {total_size_mb:.2f} MB"
    )
    
@Client.on_message(filters.command('invite') & filters.user(ADMINS))
async def gen_invite(bot, message):
    if len(message.command) == 1: return await message.reply('Gɪᴠᴇ Mᴇ A Cʜᴀᴛ Iᴅ')
    chat = message.command[1]
    try: chat = int(chat)
    except: return await message.reply('Gɪᴠᴇ Mᴇ A Vᴀʟɪᴅ Cʜᴀᴛ ID')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Iɴᴠɪᴛᴇ Lɪɴᴋ Gᴇɴᴇʀᴀᴛɪᴏɴ Fᴀɪʟᴇᴅ, Iᴀᴍ Nᴏᴛ Hᴀᴠɪɴɢ Sᴜғғɪᴄɪᴇɴᴛ Rɪɢʜᴛs")
    except Exception as e:
        return await message.reply(f'Eʀʀᴏʀ: {e}')
    await message.reply(f'Hᴇʀᴇ Iꜱ Yᴏᴜʀ Iɴᴠɪᴛᴇ Lɪɴᴋ: {link.invite_link}')

@Client.on_message(filters.command('ban_user') & filters.user(ADMINS))
async def ban_a_user(bot, message):
    if len(message.command) == 1: return await message.reply('Gɪᴠᴇ Mᴇ A Uꜱᴇʀ Iᴅ / Uꜱᴇʀɴᴀᴍᴇ')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try: chat = int(chat)
    except: pass
    try: k = await bot.get_users(chat)
    except PeerIdInvalid: return await message.reply("Tʜɪs Is Aɴ Iɴᴠᴀʟɪᴅ Usᴇʀ, Mᴀᴋᴇ Sᴜʀᴇ Iᴀ Hᴀᴠᴇ Mᴇᴛ Hɪᴍ Bᴇғᴏʀᴇ")
    except IndexError: return await message.reply("Tʜɪs Mɪɢʜᴛ Bᴇ A Cʜᴀɴɴᴇʟ, Mᴀᴋᴇ Sᴜʀᴇ Iᴛs A Usᴇʀ.")
    except Exception as e: return await message.reply(f'Eʀʀᴏʀ: {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if jar['is_banned']: return await message.reply(f"{k.mention} Iꜱ Aʟʀᴇᴅʏ Bᴀɴɴᴇᴅ\nRᴇᴀꜱᴏɴ: {jar['ban_reason']}")
        await db.ban_user(k.id, reason)
        temp.BANNED_USERS.append(k.id)
        await message.reply(f"Sᴜᴄᴄᴇꜱꜰᴜʟʟʏ Bᴀɴɴᴇᴅ {k.mention}")


    
@Client.on_message(filters.command('unban_user') & filters.user(ADMINS))
async def unban_a_user(bot, message):
    if len(message.command) == 1: return await message.reply('Gɪᴠᴇ Mᴇ A Uꜱᴇʀ Iᴅ / Uꜱᴇʀɴᴀᴍᴇ')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try: chat = int(chat)
    except: pass
    try: k = await bot.get_users(chat)
    except PeerIdInvalid: return await message.reply("Tʜɪs Is Aɴ Iɴᴠᴀʟɪᴅ Usᴇʀ, Mᴀᴋᴇ Sᴜʀᴇ Iᴀ Hᴀᴠᴇ Mᴇᴛ Hɪᴍ Bᴇғᴏʀᴇ")
    except IndexError: return await message.reply("Tʜɪs Mɪɢʜᴛ Bᴇ A Cʜᴀɴɴᴇʟ, Mᴀᴋᴇ Sᴜʀᴇ Iᴛs A Usᴇʀ.")
    except Exception as e: return await message.reply(f'Eʀʀᴏʀ: {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if not jar['is_banned']: return await message.reply(f"{k.mention} Iꜱ Nᴏᴛ Yᴇᴛ Bᴀɴɴᴇᴅ")
        await db.remove_ban(k.id)
        temp.BANNED_USERS.remove(k.id)
        await message.reply(f"Sᴜᴄᴄᴇꜱꜰᴜʟʟʏ Uɴʙᴀɴɴᴇᴅ {k.mention}")


    
@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    sps = await message.reply('Gᴇᴛᴛɪɴɢ Lɪꜱᴛ Oꜰ Uꜱᴇʀꜱ')
    users = await db.get_all_users()
    out = "Uꜱᴇʀꜱ Sᴀᴠᴇᴅ Iɴ DB Aʀᴇ:\n\n"
    async for user in users:
        out += f"<a href=tg://user?id={user['id']}>{user['name']}</a>\n"
    try:
        await sps.edit_text(out)
    except MessageTooLong:
        with open('users.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('users.txt', caption="Lɪꜱᴛ Oꜰ Uꜱᴇʀꜱ")

@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    sps = await message.reply('Gᴇᴛᴛɪɴɢ Lɪꜱᴛ Oꜰ Cʜᴀᴛꜱ')
    chats = await db.get_all_chats()
    out = "Cʜᴀᴛꜱ Sᴀᴠᴇᴅ Iɴ DB Aʀᴇ:\n\n"
    async for chat in chats:
        username = chat['username']
        username = "private" if not username else "@" + username
        out += f"**- Tɪᴛʟᴇ:** `{chat['title']}`\n**- ID:** `{chat['id']}`\n**Uꜱᴇʀɴᴀᴍᴇ:** {username}\n"
    try:
        await sps.edit_text(out)
    except MessageTooLong:
        with open('chats.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('chats.txt', caption="Lɪꜱᴛ Oꜰ Cʜᴀᴛꜱ")



@Client.on_message(filters.command('id'))
async def show_id(client, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        user_id = message.chat.id
        first = message.from_user.first_name
        last = message.from_user.last_name or ""
        username = message.from_user.username
        dc_id = message.from_user.dc_id or ""
        await message.reply_text(f"<b>➲ ꜰɪʀꜱᴛ ɴᴀᴍᴇ:</b> {first}\n<b>➲ ʟᴀꜱᴛ ɴᴀᴍᴇ:</b> {last}\n<b>➲ ᴜꜱᴇʀɴᴀᴍᴇ:</b> {username}\n<b>➲ ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ:</b> <code>{user_id}</code>\n<b>➲ ᴅᴄ ɪᴅ:</b> <code>{dc_id}</code>", quote=True)

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        _id = ""
        _id += f"<b>➲ ᴄʜᴀᴛ ɪᴅ</b>: <code>{message.chat.id}</code>\n"
        
        if message.reply_to_message:
            _id += (
                "<b>➲ ᴜꜱᴇʀ ɪᴅ</b>: "
                f"<code>{message.from_user.id if message.from_user else 'Anonymous'}</code>\n"
                "<b>➲ ʀᴇᴩʟɪᴇᴅ ᴜꜱᴇʀ ɪᴅ</b>: "
                f"<code>{message.reply_to_message.from_user.id if message.reply_to_message.from_user else 'Anonymous'}</code>\n"
            )
            file_info = get_file_id(message.reply_to_message)
        else:
            _id += (
                "<b>➲ ᴜꜱᴇʀ ɪᴅ</b>: "
                f"<code>{message.from_user.id if message.from_user else 'Anonymous'}</code>\n"
            )
            file_info = get_file_id(message)
        if file_info:
            _id += (
                f"<b>{file_info.message_type}</b>: "
                f"<code>{file_info.file_id}</code>\n"
            )
        await message.reply_text(_id, quote=True)
            

@Client.on_message(filters.command(["info"]))
async def user_info(client, message):
    status_message = await message.reply_text("`ᴩʟᴇᴀꜱᴇ ᴡᴀɪᴛ....`")
    from_user = None
    from_user_id, _ = extract_user(message)
    try:
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        return await status_message.edit(str(error))
    if from_user is None:
        return await status_message.edit("ɴᴏ ᴠᴀʟɪᴅ ᴜsᴇʀ_ɪᴅ / ᴍᴇssᴀɢᴇ sᴘᴇᴄɪғɪᴇᴅ")
    message_out_str = ""
    message_out_str += f"<b>➲ꜰɪʀꜱᴛ ɴᴀᴍᴇ:</b> {from_user.first_name}\n"
    last_name = from_user.last_name or "<b>ɴᴏɴᴇ</b>"
    message_out_str += f"<b>➲ʟᴀꜱᴛ ɴᴀᴍᴇ:</b> {last_name}\n"
    message_out_str += f"<b>➲ᴛɢ-ɪᴅ:</b> <code>{from_user.id}</code>\n"
    username = from_user.username or "<b>ɴᴏɴᴇ</b>"
    dc_id = from_user.dc_id or "[ᴜꜱᴇʀ ᴅᴏꜱᴇ'ᴛ ʜᴀᴠᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴩ]"
    message_out_str += f"<b>➲ᴅᴄ-ɪᴅ:</b> <code>{dc_id}</code>\n"
    message_out_str += f"<b>➲ᴜꜱᴇʀɴᴀᴍᴇ:</b> @{username}\n"
    message_out_str += f"<b>➲ᴜꜱᴇʀ ʟɪɴᴋ:</b> <a href='tg://user?id={from_user.id}'><b>ᴄʟɪᴄᴋ ʜᴇʀᴇ</b></a>\n"
    if message.chat.type in ((enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL)):
        try:
            chat_member_p = await message.chat.get_member(from_user.id)
            joined_date = (chat_member_p.joined_date or datetime.now()).strftime("%Y.%m.%d %H:%M:%S")
            message_out_str += f"<b>➲ᴊᴏɪɴᴇᴅ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏɴ:</b> <code>{joined_date}</code>\n"
        except UserNotParticipant: pass
    chat_photo = from_user.photo
    if chat_photo:
        local_user_photo = await client.download_media(message=chat_photo.big_file_id)
        buttons = [[InlineKeyboardButton('ᴄʟᴏꜱᴇ ✘', callback_data='close_data')]]
        await message.reply_photo(
            photo=local_user_photo,
            quote=True,
            reply_markup=InlineKeyboardMarkup(buttons),
            caption=message_out_str,
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True
        )
        os.remove(local_user_photo)
    else:
        buttons = [[InlineKeyboardButton('ᴄʟᴏꜱᴇ ✘', callback_data='close_data')]]
        await message.reply_text(
            text=message_out_str,
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True,
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True
        )
    await status_message.delete()

@Client.on_message(filters.command(["imdb", 'search']))
async def imdb_search(client, message):
    if ' ' in message.text:
        k = await message.reply('ꜱᴇᴀʀᴄʜɪɴɢ ɪᴍᴅʙ..')
        r, title = message.text.split(None, 1)
        movies = await get_poster(title, bulk=True)
        if not movies:
            return await message.reply("ɴᴏ ʀᴇꜱᴜʟᴛ ꜰᴏᴜɴᴅ")
        btn = [[InlineKeyboardButton(f"{movie.get('title')} - {movie.get('year')}", callback_data=f"imdb#{movie.movieID}")] for movie in movies ]
        await k.edit('Hᴇʀᴇ Is Wʜᴀᴛ I Fᴏᴜɴᴅ Oɴ Iᴍᴅʙ', reply_markup=InlineKeyboardMarkup(btn))
    else:
        await message.reply('Gɪᴠᴇ Mᴇ A Mᴏᴠɪᴇ / Sᴇʀɪᴇs Nᴀᴍᴇ')


@Client.on_callback_query(filters.regex('^imdb'))
async def imdb_callback(bot: Client, quer_y: CallbackQuery):
    i, movie = quer_y.data.split('#')
    imdb = await get_poster(query=movie, id=True)
    btn = [[InlineKeyboardButton(f"{imdb.get('title')}", url=imdb['url'])]]
    message = quer_y.message.reply_to_message or quer_y.message
    if imdb:
        caption = IMDB_TEMPLATE.format(
            query = imdb['title'],
            title = imdb['title'],
            votes = imdb['votes'],
            aka = imdb["aka"],
            seasons = imdb["seasons"],
            box_office = imdb['box_office'],
            localized_title = imdb['localized_title'],
            kind = imdb['kind'],
            imdb_id = imdb["imdb_id"],
            cast = imdb["cast"],
            runtime = imdb["runtime"],
            countries = imdb["countries"],
            certificates = imdb["certificates"],
            languages = imdb["languages"],
            director = imdb["director"],
            writer = imdb["writer"],
            producer = imdb["producer"],
            composer = imdb["composer"],
            cinematographer = imdb["cinematographer"],
            music_team = imdb["music_team"],
            distributors = imdb["distributors"],
            release_date = imdb['release_date'],
            year = imdb['year'],
            genres = imdb['genres'],
            poster = imdb['poster'],
            plot = imdb['plot'],
            rating = imdb['rating'],
            url = imdb['url'],
            **locals()
        )
    else:
        caption = "ɴᴏ ʀᴇꜱᴜʟᴛꜱ"
    if imdb.get('poster'):
        try:
            await quer_y.message.reply_photo(photo=imdb['poster'], caption=caption, reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            await quer_y.message.reply_photo(photo=poster, caption=caption, reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            await quer_y.message.reply(caption, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=False)
        await quer_y.message.delete()
    else:
        await quer_y.message.edit(caption, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=False)
   

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart_bot(client: Client, message: Message):
    try:
        reply = await message.reply("🔄 Restarting the bot, please wait...")
        await asyncio.sleep(2)
        await reply.delete()
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await message.reply(f"❌ Failed to restart the bot.\n**Error:** `{e}`")
        
@Client.on_message(filters.command("checkveri"))
async def check_veri(client, message: Message):
    args = message.text.split()

    # Only allow checking self
    if len(args) > 1:
        return await message.reply("⚠️ You can only check your own verification status.", quote=True)

    user_id = message.from_user.id

    # Step 2: Fetch verification data
    data = await db.get_verified(user_id)
    date_str = data.get('date', "1999-12-31")
    time_str = data.get('time', "23:59:59")
    verified_dt_str = f"{date_str} {time_str}"
    default_dt_str = "1999-12-31 23:59:59"

    tz = pytz.timezone("Asia/Kolkata")

    # Step 3: Handle unverified users
    if verified_dt_str == default_dt_str:
        return await message.reply("🟡 You haven't verified yet. Please verify to activate your access.", quote=True)

    try:
        # Parse verification time
        verified_dt = tz.localize(datetime.strptime(verified_dt_str, "%Y-%m-%d %H:%M:%S"))
        expiry_dt = verified_dt + timedelta(hours=12)
        now = datetime.now(tz)
        time_left = expiry_dt - now

        # Format datetime values
        if USE_12_HOUR_FORMAT:
            verified_fmt = verified_dt.strftime("%d %b %Y, %I:%M:%S %p IST")
            expiry_fmt = expiry_dt.strftime("%d %b %Y, %I:%M:%S %p IST")
        else:
            verified_fmt = verified_dt.strftime("%d %b %Y, %H:%M:%S IST")
            expiry_fmt = expiry_dt.strftime("%d %b %Y, %H:%M:%S IST")

        # Expired case
        if time_left.total_seconds() <= 0:
            return await message.reply(
                f"⛔ **Verification Expired!**\n\n"
                f"🗓️ Last Verified On : `{verified_fmt}`\n"
                f"❌ Expired At       : `{expiry_fmt}`", quote=True)

        # Format time left
        hrs, rem = divmod(int(time_left.total_seconds()), 3600)
        mins, secs = divmod(rem, 60)
        time_left_fmt = f"{hrs}h {mins}m {secs}s"

        # Success message
        await message.reply(
            f"✅ **You're Verified**\n\n"
            f"🗓️ Verified On  : `{verified_fmt}`\n"
            f"⏳ Expires In   : `{time_left_fmt}`\n"
            f"📌 Expires At   : `{expiry_fmt}`", quote=True)

    except Exception as e:
        await message.reply(f"❌ Error checking verification data.\n\nDetails: `{e}`", quote=True)


# 📋 /veridata - Show all verified users
@Client.on_message(filters.command("veridata") & filters.user(ADMINS))
async def show_verified_users(client, message: Message):
    users_cursor = await db.get_all_users()
    verified_list = []

    async for user in users_cursor:
        status = user.get("verification_status")
        if status and status.get("date") != "1999-12-31":
            user_id = user["id"]
            name = user.get("name", "Unknown")
            date = status["date"]
            time = status["time"]
            verified_list.append(f"🆔 `{user_id}` - **{name}**\n📅 Date: `{date}` 🕒 Time: `{time}`\n")

    if not verified_list:
        return await message.reply("😔 No verified users found.")

    header = f"**✅ Verified Users List: Total {len(verified_list)} users verified**\n\n"
    result_text = header + "\n".join(verified_list)

    if len(result_text) > 4096:
        with open("verified_users.txt", "w", encoding="utf-8") as f:
            f.write(result_text)
        await message.reply_document("verified_users.txt", quote=True)
    else:
        await message.reply(result_text, quote=True)

# 📅 /veridata_date - Show verified users grouped by date
@Client.on_message(filters.command("veridata_date") & filters.user(ADMINS))
async def show_verified_users_by_date(client, message: Message):
    users_cursor = await db.get_all_users()
    date_wise_data = defaultdict(list)

    async for user in users_cursor:
        status = user.get("verification_status")
        if status and status.get("date") != "1999-12-31":
            date = status["date"]
            user_id = user["id"]
            name = user.get("name", "Unknown")
            time = status["time"]
            date_wise_data[date].append(f"🆔 `{user_id}` - **{name}** 🕒 `{time}`")

    if not date_wise_data:
        return await message.reply("😔 No verified users found.")

    output_lines = ["**📅 Verified Users Grouped by Date:**\n"]
    for date in sorted(date_wise_data):
        output_lines.append(f"📆 **{date}** - {len(date_wise_data[date])} users")
        output_lines.extend(date_wise_data[date])
        output_lines.append("")

    final_text = "\n".join(output_lines)

    if len(final_text) > 4096:
        with open("verified_users_by_date.txt", "w", encoding="utf-8") as f:
            f.write(final_text)
        await message.reply_document("verified_users_by_date.txt", quote=True)
    else:
        await message.reply(final_text, quote=True)
        
@Client.on_message(filters.command("banz") & filters.user(ADMINS))
async def ban_user_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("⚠️ Usage: /ban <user_id> [reason]")
        user_id = int(args[1])
        reason = " ".join(args[2:]) or "No reason"
        await db.ban_user(user_id, reason)
        await message.reply(f"✅ Banned user {user_id} for: {reason}")
    except ValueError:
        await message.reply("❌ Invalid user ID.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("unbanz") & filters.user(ADMINS))
async def unban_user_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /unban <user_id>")
        user_id = int(args[1])
        await db.remove_ban(user_id)
        await message.reply(f"✅ Unbanned user {user_id}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("isban") & filters.user(ADMINS))
async def is_ban_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /isban <user_id>")
        user_id = int(args[1])
        status = await db.get_ban_status(user_id)
        if status["is_banned"]:
            await message.reply(f"🚫 User {user_id} is banned.\nReason: {status['ban_reason']}")
        else:
            await message.reply(f"✅ User {user_id} is not banned.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("deluser") & filters.user(ADMINS))
async def delete_user_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /deluser <user_id>")
        user_id = int(args[1])
        await db.delete_user(user_id)
        await message.reply(f"🗑️ Deleted user {user_id} from DB.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("userscount") & filters.user(ADMINS))
async def total_users_cmd(client, message: Message):
    try:
        count = await db.total_users_count()
        await message.reply(f"👥 Total users in DB: {count}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("getbanned") & filters.user(ADMINS))
async def get_banned_cmd(client, message: Message):
    try:
        users, chats = await db.get_banned()
        await message.reply(f"🚫 Banned Users: {len(users)}\n📛 Disabled Groups: {len(chats)}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("verify") & filters.user(ADMINS))
async def verify_user_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /verify <user_id>")
        user_id = int(args[1])
        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        await db.update_verification(user_id, now.date(), now.time())
        await message.reply(f"✅ User {user_id} marked as verified.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("checkverii") & filters.user(ADMINS))
async def check_veri_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /checkveri <user_id>")
        user_id = int(args[1])
        status = await db.get_verified(user_id)
        await message.reply(f"✅ Verified on: {status['date']} at {status['time']}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("chatscount") & filters.user(ADMINS))
async def total_chats_cmd(client, message: Message):
    try:
        count = await db.total_chat_count()
        await message.reply(f"💬 Total groups in DB: {count}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("dbsize") & filters.user(ADMINS))
async def db_size_cmd(client, message: Message):
    try:
        size = await db.get_db_size()
        await message.reply(f"🗃️ DB Size: {round(size / 1024, 2)} KB")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("disablechat") & filters.user(ADMINS))
async def disable_chat_cmd(client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        if len(args) < 2:
            return await message.reply("⚠️ Usage: /disablechat <chat_id> [reason]")
        chat_id = int(args[1])
        reason = args[2] if len(args) > 2 else "No Reason"
        await db.disable_chat(chat_id, reason)
        await message.reply(f"🚫 Disabled chat {chat_id}. Reason: {reason}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
        
@Client.on_message(filters.command("delchat") & filters.user(ADMINS))
async def delete_chat_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /delchat <chat_id>")
        chat_id = int(args[1])
        await db.delete_chat(chat_id)
        await message.reply(f"🗑️ Deleted chat {chat_id} from DB.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("saveinvite") & filters.user(ADMINS))
async def save_invite_cmd(client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        if len(args) != 3:
            return await message.reply("⚠️ Usage: /saveinvite <chat_id> <invite_link>")
        chat_id = int(args[1])
        link = args[2]
        await db.save_chat_invite_link(chat_id, link)
        await message.reply(f"🔗 Saved invite link for chat {chat_id}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
@Client.on_message(filters.command("invite") & filters.user(ADMINS))
async def get_invite_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /invite <chat_id>")
        chat_id = int(args[1])
        link = await db.get_chat_invite_link(chat_id)
        if link:
            await message.reply(f"🔗 Invite link for chat {chat_id}: {link}")
        else:
            await message.reply("❌ No invite link found for this chat.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        

@Client.on_message(filters.command("settingz") & filters.user(ADMINS))
async def get_settings_cmd(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("⚠️ Usage: /settings <chat_id>")
        chat_id = int(args[1])
        settings = await db.get_settings(chat_id)
        await message.reply(f"⚙️ Settings forr {chat_id}:\n{settings}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
        
@Client.on_message(filters.command("listallcommands") & filters.user(ADMINS))
async def list_all_commands(client, message):
    try:
        commands_dict = list_commands_in_project(".")
        if not commands_dict:
            await message.reply("No commands found in the project.")
            return

        max_len = 4096
        current_msg = ""
        all_msgs = []

        def flush():
            nonlocal current_msg
            if current_msg.strip():
                all_msgs.append(current_msg.strip())
                current_msg = ""

        for filename, command_entries in commands_dict.items():
            file_header = f"\n📁 <code>{filename}</code>:\n"
            file_block = file_header
            for cmd_list, is_admin in command_entries:
                tag = "👮‍♂️ (Admin)" if is_admin else ""
                cmds_str = ", ".join([f"/{cmd}" for cmd in cmd_list])
                file_block += f" • {cmds_str} {tag}\n"

            if len(current_msg) + len(file_block) > max_len:
                flush()

            # if still too big, even alone
            if len(file_block) > max_len:
                # split lines safely
                lines = file_block.splitlines(keepends=True)
                temp_block = ""
                for line in lines:
                    if len(temp_block) + len(line) > max_len:
                        all_msgs.append(temp_block)
                        temp_block = ""
                    temp_block += line
                if temp_block:
                    all_msgs.append(temp_block)
                current_msg = ""
            else:
                current_msg += file_block

        flush()

        for i, part in enumerate(all_msgs):
            await message.reply(part, quote=True)

    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")
        

@Client.on_message(filters.command("uptime") & filters.private)
async def get_uptime(client, message):
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    uptime_dt = datetime.fromtimestamp(UPTIME, tz=tz)
    diff = now - uptime_dt

    days, seconds = diff.days, diff.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    uptime_str = ""
    if days > 0:
        uptime_str += f"{days} Day(s), "
    if hours > 0:
        uptime_str += f"{hours} Hour(s), "
    if minutes > 0:
        uptime_str += f"{minutes} Minute(s), "
    uptime_str += f"{seconds} Second(s)"

    await message.reply_text(
        f"🤖 <b>Bot Uptime:</b>\n⏱️ <code>{uptime_str}</code>",
        quote=True
    )
    
