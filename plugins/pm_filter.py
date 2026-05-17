import asyncio
import re
import math
import logging
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from info import AUTH_USERS, PM_IMDB, SINGLE_BUTTON, PROTECT_CONTENT, IMDB_TEMPLATE, IMDB_DELET_TIME, PMFILTER, G_FILTER, SHORT_URL, SHORT_API
from utils import get_size, get_shortlink, get_poster, search_gagala, temp
from database.ia_filterdb import get_search_results
from plugins.group_filter import global_filters

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Keep page sizes consistent
PAGE_SIZE = 10

@Client.on_message(filters.private & filters.text & filters.incoming)
async def auto_pm_fill(b, m):
    if not PMFILTER:
        return
    if AUTH_USERS and m.from_user.id not in AUTH_USERS:
        return
    if re.findall(r"((^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", m.text): 
        return
    if G_FILTER:
        kd = await global_filters(b, m)
        if kd is False: 
            await pm_AutoFilter(b, m)
    else: 
        await pm_AutoFilter(b, m)

@Client.on_callback_query(filters.create(lambda _, __, query: query.data.startswith("pmnext")))
async def pm_next_page(bot, query):
    try:
        _, req, key, offset = query.data.split("_")
        offset = int(offset)
    except ValueError:
        offset = 0

    search = temp.PM_BUTTONS.get(str(key))
    if not search: 
        return await query.answer("Yᴏᴜ Aʀᴇ Usɪɴɢ Oɴᴇ Oғ Mʏ Oʟᴅ Mᴇssᴀɢᴇs, Pʟᴇᴀsᴇ Sᴇɴᴅ Tʜᴇ Rᴇǫᴜᴇsᴛ Aɢᴀɪɴ", show_alert=True)

    files, n_offset, total = await get_search_results(search.lower(), offset=offset, filter=True)
    try: 
        n_offset = int(n_offset)
    except ValueError: 
        n_offset = 0
        
    if not files: 
        return
    
    if SHORT_URL and SHORT_API:          
        if SINGLE_BUTTON:
            btn = [[InlineKeyboardButton(text=f"[{get_size(file.file_size)}] {file.file_name}", url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}"))] for file in files ]
        else:
            btn = [[InlineKeyboardButton(text=f"{file.file_name}", url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}")),
                    InlineKeyboardButton(text=f"{get_size(file.file_size)}", url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}"))] for file in files ]
    else:        
        if SINGLE_BUTTON:
            btn = [[InlineKeyboardButton(text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'pmfile#{file.file_id}')] for file in files ]
        else:
            btn = [[InlineKeyboardButton(text=f"{file.file_name}", callback_data=f'pmfile#{req}#{file.file_id}'),
                    InlineKeyboardButton(text=f"{get_size(file.file_size)}", callback_data=f'pmfile#{file.file_id}')] for file in files ]

    btn.insert(0, [InlineKeyboardButton("🔗 ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ 🔗", "howdl")])
    
    off_set = 0 if 0 < offset <= PAGE_SIZE else (None if offset == 0 else offset - PAGE_SIZE)
    
    current_page = math.ceil(int(offset) / PAGE_SIZE) + 1
    total_pages = math.ceil(total / PAGE_SIZE)

    if n_offset == 0:
        btn.append([
            InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data=f"pmnext_{req}_{key}_{off_set}"),
            InlineKeyboardButton(f"❄️ ᴩᴀɢᴇꜱ {current_page} / {total_pages}", callback_data="pages")
        ])
    elif off_set is None:
        btn.append([
            InlineKeyboardButton(f"❄️ {current_page} / {total_pages}", callback_data="pages"),
            InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"pmnext_{req}_{key}_{n_offset}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data=f"pmnext_{req}_{key}_{off_set}"),
            InlineKeyboardButton(f"❄️ {current_page} / {total_pages}", callback_data="pages"),
            InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"pmnext_{req}_{key}_{n_offset}")
        ])
        
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.create(lambda _, __, query: query.data.startswith("pmspolling")))
async def pm_spoll_tester(bot, query):
    _, user, movie_ = query.data.split('#')
    if movie_ == "close_spellcheck":
        try:
            return await query.message.delete()
        except Exception:
            return

    movies = temp.PM_SPELL.get(str(query.message.reply_to_message.id)) if query.message.reply_to_message else None
    if not movies:
        return await query.answer("Yᴏᴜ Aʀᴇ Usɪɴɢ Oɴᴇ Oғ Mʏ Oʟᴅ Mᴇssᴀɢᴇs, Pʟᴇᴀsᴇ Sᴇɴᴅ Tʜᴇ Rᴇǫᴜᴇsᴛ Aɢᴀɪɴ", show_alert=True)
    
    try:
        movie = movies[int(movie_)]
    except (IndexError, ValueError):
        return await query.answer("Sᴘᴇʟʟᴄʜᴇᴄᴋ sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ.", show_alert=True)

    await query.answer('Cʜᴇᴄᴋɪɴɢ Fᴏʀ Mᴏᴠɪᴇ Iɴ Dᴀᴛᴀʙᴀsᴇ...')
    files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await pm_AutoFilter(bot, query, k)
    else:
        k = await query.message.edit('Tʜɪs Mᴏᴠɪᴇ Nᴏᴛ Fᴏᴜɴᴅ Iɴ Dᴀᴛᴀʙᴀsᴇ')
        await asyncio.sleep(10)
        try:
            await k.delete()
        except Exception:
            pass

async def pm_AutoFilter(client, msg, pmspoll=False):    
    if not pmspoll:
        message = msg
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files: 
                return await pm_spoll_choker(msg)              
        else: 
            return 
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = pmspoll

    pre = 'pmfilep' if PROTECT_CONTENT else 'pmfile'
    req = message.from_user.id if (message and message.from_user) else 0

    if SHORT_URL and SHORT_API:          
        if SINGLE_BUTTON:
            btn = [[InlineKeyboardButton(text=f"[{get_size(file.file_size)}] {file.file_name}", url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=pre_{file.file_id}"))] for file in files ]
        else:
            btn = [[InlineKeyboardButton(text=f"{file.file_name}", url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=pre_{file.file_id}")),
                    InlineKeyboardButton(text=f"{get_size(file.file_size)}", url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=pre_{file.file_id}"))] for file in files ]
    else:        
        if SINGLE_BUTTON:
            btn = [[InlineKeyboardButton(text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'{pre}#{file.file_id}')] for file in files ]
        else:
            btn = [[InlineKeyboardButton(text=f"{file.file_name}", callback_data=f'{pre}#{req}#{file.file_id}'),
                    InlineKeyboardButton(text=f"{get_size(file.file_size)}", callback_data=f'{pre}#{file.file_id}')] for file in files ]    

    btn.insert(0, [InlineKeyboardButton("🔗 ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ 🔗", "howdl")])
    
    if offset != "":
        key = f"{message.id}" if message else "0"
        temp.PM_BUTTONS[key] = search
        btn.append([
            InlineKeyboardButton(text=f"❄️ ᴩᴀɢᴇꜱ 1/{math.ceil(int(total_results) / PAGE_SIZE)}", callback_data="pages"),
            InlineKeyboardButton(text="ɴᴇxᴛ ➡️", callback_data=f"pmnext_{req}_{key}_{offset}")
        ])
    else:
        btn.append([InlineKeyboardButton(text="❄️ ᴩᴀɢᴇꜱ 1/1", callback_data="pages")])

    imdb = await get_poster(search) if PM_IMDB else None
    
    if imdb:
        cap = IMDB_TEMPLATE.format(
            group=message.chat.title if message.chat else "Private",
            requested=message.from_user.mention if message.from_user else "Unknown",
            query=search,
            title=imdb.get('title', 'N/A'),
            votes=imdb.get('votes', 'N/A'),
            aka=imdb.get('aka', 'N/A'),
            seasons=imdb.get('seasons', 'N/A'),
            box_office=imdb.get('box_office', 'N/A'),
            localized_title=imdb.get('localized_title', 'N/A'),
            kind=imdb.get('kind', 'N/A'),
            imdb_id=imdb.get('imdb_id', 'N/A'),
            cast=imdb.get('cast', 'N/A'),
            runtime=imdb.get('runtime', 'N/A'),
            countries=imdb.get('countries', 'N/A'),
            certificates=imdb.get('certificates', 'N/A'),
            languages=imdb.get('languages', 'N/A'),
            director=imdb.get('director', 'N/A'),
            writer=imdb.get('writer', 'N/A'),
            producer=imdb.get('producer', 'N/A'),
            composer=imdb.get('composer', 'N/A'),
            cinematographer=imdb.get('cinematographer', 'N/A'),
            music_team=imdb.get('music_team', 'N/A'),
            distributors=imdb.get('distributors', 'N/A'),
            release_date=imdb.get('release_date', 'N/A'),
            year=imdb.get('year', 'N/A'),
            genres=imdb.get('genres', 'N/A'),
            poster=imdb.get('poster', ''),
            plot=imdb.get('plot', 'N/A'),
            rating=imdb.get('rating', 'N/A'),
            url=imdb.get('url', '')
        )
    else:
        cap = f"Hᴇʀᴇ Is Wʜᴀᴛ I Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Qᴜᴇʀʏ {search}"

    reply_msg = None
    if imdb and imdb.get('poster'):
        try:
            reply_msg = await message.reply_photo(photo=imdb.get('poster'), caption=cap, quote=True, reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            poster = imdb.get('poster').replace('.jpg', "._V1_UX360.jpg")
            try:
                reply_msg = await message.reply_photo(photo=poster, caption=cap, quote=True, reply_markup=InlineKeyboardMarkup(btn))
            except Exception:
                reply_msg = await message.reply_text(cap, quote=True, reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            reply_msg = await message.reply_text(cap, quote=True, reply_markup=InlineKeyboardMarkup(btn))
    else:
        reply_msg = await message.reply_text(cap, quote=True, reply_markup=InlineKeyboardMarkup(btn))

    if pmspoll and msg.message:
        try:
            await msg.message.delete()
        except Exception:
            pass

    if reply_msg and IMDB_DELET_TIME:
        await asyncio.sleep(IMDB_DELET_TIME)
        try:
            await reply_msg.delete()
        except Exception:
            pass

async def pm_spoll_choker(msg):
    query = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)", "", msg.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    
    if not g_s:
        k = await msg.reply("I Cᴏᴜʟᴅɴ'TL Fɪɴᴅ Aɴʏ Mᴏᴠɪᴇ Iɴ Tʜᴀᴛ Nᴀᴍᴇ", quote=True)
        await asyncio.sleep(10)
        try: return await k.delete()
        except Exception: return

    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)', '', i, flags=re.IGNORECASE) for i in gs]
    
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*", re.IGNORECASE)
        for mv in g_s:
            match = reg.match(mv)
            if match: gs_parsed.append(match.group(1))

    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))
    if len(gs_parsed) > 3: 
        gs_parsed = gs_parsed[:3]
        
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)
            if imdb_s: 
                movielist += [movie.get('title') for movie in imdb_s]
                
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))
    
    if not movielist:
        k = await msg.reply("I Cᴏᴜʟᴅɴ'ᴛ Fɪɴᴅ Aɴʏᴛʜɪɴɢ Rᴇʟᴀᴛᴇᴅ Tᴏ Tʜᴀᴛ. Cʜᴇᴄᴋ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ", quote=True)
        await asyncio.sleep(10)
        try: return await k.delete()
        except Exception: return

    temp.PM_SPELL[str(msg.id)] = movielist
    btn = [[InlineKeyboardButton(text=movie.strip(), callback_data=f"pmspolling#{user}#{k}")] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'pmspolling#{user}#close_spellcheck')])
    await msg.reply("I Cᴏᴜʟᴅɴ'ᴛ Fɪɴᴅ Aɴʏᴛʜɪɴɢ Rᴇʟᴀᴛᴇᴅ Tᴏ Tʜᴀᴛ. Dɪᴅ Yᴏᴜ Mᴇᴀɴ Aɴʏ Oɴᴇ Oғ Tʜᴇsᴇ?", reply_markup=InlineKeyboardMarkup(btn), quote=True)
