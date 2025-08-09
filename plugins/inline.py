import logging
from pyrogram import Client, emoji, filters
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedDocument,
    InlineQuery
)

from database.ia_filterdb import get_search_results
from database.users_chats_db import db
from utils import is_subscribed, get_size, temp, check_verification
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, LOG_CHANNEL, PREMIUM_MODE
from Script import script

logger = logging.getLogger(__name__)

# Updated cache_time logic: if premium mode is on, always set to 0 (no caching)
cache_time = 0 if (AUTH_USERS or AUTH_CHANNEL or PREMIUM_MODE) else CACHE_TIME


@Client.on_inline_query()
async def answer(bot, query: InlineQuery):
    """Inline query handler following the 5-step rule system."""

    user_id = query.from_user.id

    # Step 1: Check if user is blocked
    if user_id in temp.BANNED_USERS:
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="⚠️ You are not allowed to use this bot.",
            switch_pm_parameter="not_allowed"
        )
        return

    # Step 2: Check if AUTH_CHANNEL is set
    if AUTH_CHANNEL:
        # Step 3: Check subscription
        if not await is_subscribed(bot, query):
            await query.answer(
                results=[],
                cache_time=0,
                switch_pm_text="📢 Join our channel to use this bot.",
                switch_pm_parameter="subscribe"
            )
            return

    # Step 4: Check PREMIUM_MODE
    if PREMIUM_MODE:
        # Step 5: Verify premium user
        if not await check_verification(bot, user_id):
            await query.answer(
                results=[],
                cache_time=0,
                switch_pm_text="💎 Premium Only - ₹99\nTap to Buy Premium",
                switch_pm_parameter="premium"
            )
            return

    results = []
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)
    files, next_offset, total = await get_search_results(string,
                                                         file_type=file_type,
                                                         max_results=10,
                                                         offset=offset)

    for file in files:
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{file.file_name}"
        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {get_size(file.file_size)}\nType: {file.file_type}',
                reply_markup=reply_markup))

    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}"
        if string:
            switch_pm_text += f" for {string}"
        try:
            await query.answer(results=results,
                               is_personal=True,
                               cache_time=cache_time,
                               switch_pm_text=switch_pm_text,
                               switch_pm_parameter="start",
                               next_offset=str(next_offset))
        except QueryIdInvalid:
            pass
        except Exception as e:
            logging.exception(str(e))
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No results'
        if string:
            switch_pm_text += f' for "{string}"'

        await query.answer(results=[],
                           is_personal=True,
                           cache_time=cache_time,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="okay")


def get_reply_markup(query):
    buttons = [
        [
            InlineKeyboardButton('Search again', switch_inline_query_current_chat=query)
        ]
    ]
    return InlineKeyboardMarkup(buttons)
