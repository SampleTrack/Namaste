import logging
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument, InlineQuery
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, ADMINS

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME


async def is_authorized(query: InlineQuery) -> bool:
    """Returns True only if user is an admin or in AUTH_USERS list."""
    user_id = query.from_user.id if query.from_user else None
    if not user_id:
        return False
    if user_id in (ADMINS or []):
        return True
    if AUTH_USERS and user_id in AUTH_USERS:
        return True
    return False


@Client.on_inline_query()
async def answer(bot, query):
    # Block all non-authorized users
    if not await is_authorized(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="🚫 This feature is for authorized users only",
            switch_pm_parameter="unauthorized"
        )
        return

    # Check channel subscription (only relevant for auth users if you want)
    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="📢 Subscribe to the channel to continue",
            switch_pm_parameter="subscribe"
        )
        return

    # Parse query string and optional file type filter
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)
    files, next_offset, total = await get_search_results(
        string, file_type=file_type, max_results=10, offset=offset
    )

    results = []
    for file in files:
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    mention=query.from_user.mention,
                    file_name=title or '',
                    file_size=size or '',
                    file_caption=f_caption or ''
                )
            except Exception as e:
                logger.exception(e)

        if not f_caption:
            f_caption = file.file_name

        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {size}\nType: {file.file_type}',
                reply_markup=reply_markup
            )
        )

    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}"
        if string:
            switch_pm_text += f" for {string}"
        try:
            await query.answer(
                results=results,
                is_personal=True,
                cache_time=cache_time,
                switch_pm_text=switch_pm_text,
                switch_pm_parameter="start",
                next_offset=str(next_offset)
            )
        except QueryIdInvalid:
            pass
        except Exception as e:
            logger.exception(str(e))
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No Results'
        if string:
            switch_pm_text += f' for "{string}"'
        await query.answer(
            results=[],
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter="okay"
        )


def get_reply_markup(query):
    buttons = [[InlineKeyboardButton('⟳ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ', switch_inline_query_current_chat=query)]]
    return InlineKeyboardMarkup(buttons)
    
